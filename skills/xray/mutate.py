from __future__ import annotations

import re
from pathlib import Path
from .scope import matching_lines
from .risk import rank_risk
from .git import search_history, GitError
from .github import search_discussion
from .requirements import concepts, normalize_unit

CHANGE_RE = re.compile(
    r"(?P<old>[0-9]+(?:\.[0-9]+)?)\s*(?P<old_unit>KB|KiB|MB|MiB|GB|GiB|TB|TiB|bytes?|b|ms|milliseconds?|s|sec|secs|second|seconds|min|mins|minute|minutes|m|rpm|rps|/min|/minute|/s|/sec|%|decimals?|decimal(?:\s+places)?)?\s*(?:→|->|to)\s*(?P<new>[0-9]+(?:\.[0-9]+)?)\s*(?P<new_unit>KB|KiB|MB|MiB|GB|GiB|TB|TiB|bytes?|b|ms|milliseconds?|s|sec|secs|second|seconds|min|mins|minute|minutes|m|rpm|rps|/min|/minute|/s|/sec|%|decimals?|decimal(?:\s+places)?)?",
    re.I,
)


def parse_change(change):
    m = CHANGE_RE.search(change)
    if not m:
        return None
    d = m.groupdict()
    old_unit = normalize_unit(d["old_unit"])
    new_unit = normalize_unit(d["new_unit"])
    # A bare "2 decimals" is a precision change, not a time/size unit.
    if d["old_unit"] and d["old_unit"].lower().startswith("decimal"):
        old_unit = new_unit = "decimals"
    return {"old": float(d["old"]), "old_unit": old_unit, "new": float(d["new"]), "new_unit": new_unit}


def _semantic_terms(change):
    parsed = parse_change(change)
    found = set(concepts(change))
    low = change.lower()
    if "decimal" in low or "precision" in low:
        found.add("precision")
    if parsed:
        unit = parsed["old_unit"] or parsed["new_unit"]
        if unit in {"mb", "gb", "kb", "tb"}:
            found.update({"size"})
        elif unit in {"ms", "s", "min", "h"}:
            found.add("timeout")
        elif unit in {"rpm", "rps"}:
            found.add("rate")
    # Search terms are concrete repository vocabulary, not just abstract
    # categories. This keeps deterministic discovery broad enough to find
    # implementation/config anchors without matching every generic "size" or
    # "timeout" occurrence.
    domain_patterns = {
        "size": ["upload", "payload", "max_body", "body_bytes", "max_upload", "client_max_body_size", "request_size"],
        "timeout": ["timeout", "deadline", "request_timeout", "visibility_timeout"],
        "rate": ["rate_limit", "requests_per_minute", "requests/minute", "scope", "rpm"],
        "precision": ["decimal", "precision", "currency", "minor_units", "round"],
        "retry": ["retry", "retries", "backoff", "attempt"],
        "queue": ["queue", "visibility", "lease"],
        "auth": ["auth", "tls", "permission"],
        "pii": ["pii", "redact", "customer_email"],
        "inventory": ["inventory", "reservation", "atomic"],
        "idempotency": ["idempotency", "duplicate", "provider"],
    }
    concrete = []
    for domain in found:
        concrete.extend(domain_patterns.get(domain, []))
    return list(dict.fromkeys(concrete))


def _value_variants(parsed):
    if not parsed:
        return []
    vals = []
    for k in ("old", "new"):
        v, u = parsed[k], parsed[k + "_unit"]
        if u == "decimals":
            vals.extend([f"{v:g} decimals", f"{v:g} decimal"])
        else:
            vals.extend([f"{v:g}{u}", f"{v:g} {u}"])
            if v.is_integer():
                raw = str(int(v))
                if len(raw) > 3:
                    vals.append(f"{int(v):_}")
        if u in {"mb", "gb", "kb", "tb"}:
            factors = {"kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4}
            b = v * factors[u]
            vals += [f"{int(b)}", f"{int(b):,}"]
    return vals


def _match_quality(change_concepts, snippet, parsed):
    """Return (score, kind, confidence) for a mutation candidate.

    ``direct_value`` means the requested old/new quantity is visible in the
    anchor (including common byte encodings). ``semantic_anchor`` means the
    line is relevant to the concept but does not prove that the exact value is
    controlled there. The latter is intentionally lower-confidence so callers
    do not mistake candidate impact sites for confirmed mutation sites.
    """
    sc = concepts(snippet)
    low = snippet.lower()
    score = 0
    direct = False
    if change_concepts & sc:
        score += 4
    if parsed:
        for k in ("old", "new"):
            v, u = parsed[k], parsed[k + "_unit"]
            variants = (f"{v:g}{u}", f"{v:g} {u}") if u else (f"{v:g}",)
            if any(x in low for x in variants):
                score += 5
                direct = True
            # Match numeric source literals with separators (500_000), and
            # duration encodings such as time.Duration(60) * time.Second.
            numeric = str(int(v)) if v.is_integer() else str(v)
            if v.is_integer():
                numeric_re = "_?".join(re.escape(ch) for ch in numeric)
            else:
                numeric_re = re.escape(numeric)
            if re.search(rf"(?<![A-Za-z0-9_]){numeric_re}(?![A-Za-z0-9_])", low):
                if u in {"mb", "gb", "kb", "tb", "bytes", "b", "ms", "s", "min", "h", "rpm", "rps", "decimals"} or (u == "" and change_concepts & {"size", "timeout", "rate", "precision"}):
                    score += 3
                    direct = True
            if u in {"mb", "gb", "kb", "tb"} and ("1024" in low or "bytes" in low):
                if re.search(rf"\b{int(v) if v.is_integer() else v}\b", low):
                    score += 3
                    direct = True
    if any(x in low for x in ("test", "assert", "expected")):
        score += 1
    if direct:
        return score, "direct_value", 0.97
    return score, "semantic_anchor", 0.72

def mutate(root, change, patterns=None, include_github=False):
    root = Path(root).resolve()
    parsed = parse_change(change)
    semantic = patterns or _semantic_terms(change)
    values = _value_variants(parsed)
    search_patterns = list(dict.fromkeys(semantic + values))
    hits = []
    cc = concepts(change)
    for p, line, snippet in matching_lines(root, search_patterns):
        score, match_kind, confidence = _match_quality(cc, snippet, parsed)
        # A semantic-only anchor is useful for impact analysis, but should not
        # dominate exact-value evidence. Require at least one concept match.
        if score < 4:
            continue
        rel = str(p.relative_to(root))
        category = "test" if "/test" in rel.lower() or rel.lower().startswith("test") else "config" if p.suffix.lower() in {".yml", ".yaml", ".toml", ".ini", ".conf", ".env"} or "config" in rel.lower() else "docs" if p.suffix.lower() in {".md", ".rst", ".txt"} else "code"
        hits.append({"source_type": "repository", "locator": {"file": rel, "line": line}, "snippet": snippet, "strength": "direct" if match_kind == "direct_value" else "inferred", "polarity": "context", "relevance_score": score, "category": category, "match_kind": match_kind, "confidence": confidence})
    hits.sort(key=lambda x: (-x["relevance_score"], x["locator"]["file"], x["locator"]["line"]))

    history = []
    history_errors = []
    seen_patterns = set()
    for pattern in semantic[:8] + values[:8]:
        if len(pattern) < 3 or pattern in seen_patterns:
            continue
        seen_patterns.add(pattern)
        try:
            history.extend(search_history(root, re.escape(pattern), limit=10))
        except GitError as exc:
            history_errors.append(str(exc))
    unique_history = {x["commit"]: x for x in history}.values()
    github = {"issues": [], "pull_requests": []}
    if include_github and semantic:
        github = search_discussion(root, " OR ".join(semantic[:4]), limit=10, hydrate=True)

    impacts = [{"type": h["category"], "location": h["locator"], "reason": (
        "Exact value/encoding match; likely mutation control point." if h["match_kind"] == "direct_value"
        else "Semantic candidate anchor; exact mutation control is not proven here."
    ), "confidence": h["confidence"], "match_kind": h["match_kind"]} for h in hits]
    risk = rank_risk(change + " " + " ".join(h["snippet"] for h in hits[:20]), hits, "VERIFIED" if hits else "UNVERIFIED", mutation=True)
    return {
        "schema_version": "1.0", "change": change, "parsed": parsed,
        "search_patterns": search_patterns, "matches": hits,
        "git_history": list(unique_history), "git_errors": history_errors, "github": github, "impacts": impacts, "risk": risk,
        "notes": ["Matches are ranked candidate mutation sites; no file is modified automatically.", "Metadata fixtures are excluded by default.", "Direct-value matches are evidence of a concrete control point; semantic anchors are impact candidates and require review.", "Dependency semantics require review of the concrete anchors before mutation is applied."] + (["Git history collection reported errors: " + "; ".join(history_errors)] if history_errors else [])
    }
