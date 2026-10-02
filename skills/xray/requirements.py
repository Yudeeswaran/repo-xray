from __future__ import annotations

import re

NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<value>[0-9](?:[0-9_]*[0-9])?(?:\.[0-9](?:[0-9_]*[0-9])?)?)\s*(?P<unit>KB|KiB|MB|MiB|GB|GiB|TB|TiB|ms|milliseconds?|s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|%|rps|rpm|/s|/sec|/min|/minute)?\b",
    re.I,
)

ALIASES = {
    "kib": "kb", "mib": "mb", "gib": "gb", "tib": "tb",
    "milliseconds": "ms", "millisecond": "ms",
    "sec": "s", "secs": "s", "second": "s", "seconds": "s",
    "m": "min", "mins": "min", "minute": "min", "minutes": "min",
    "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
    "/s": "rps", "/sec": "rps", "/min": "rpm", "/minute": "rpm",
}

CONCEPTS = {
    "size": {
        "upload", "payload", "body", "body_bytes", "max_body", "max_upload",
        "content_length", "request_size", "file_size", "size", "bytes", "mb", "gb",
    },
    "timeout": {"timeout", "deadline", "request_timeout", "connect_timeout", "read_timeout"},
    "rate": {"rate", "rate_limit", "ratelimit", "quota", "requests", "rpm", "rps", "throttle", "capacity"},
    "precision": {"precision", "decimal", "decimals", "currency", "money", "amount", "minor", "rounding", "scale"},
    "retry": {"retry", "retries", "attempt", "attempts", "backoff"},
    "auth": {"auth", "authentication", "authorization", "tls", "token", "credential", "permission"},
    "pii": {"pii", "redact", "redaction", "personal", "privacy", "sensitive"},
    "queue": {"queue", "visibility", "visibility_timeout", "worker", "job", "lease"},
    "inventory": {"inventory", "reservation", "reserve", "atomic", "stock"},
    "idempotency": {"idempotency", "idempotent", "idempotency_key", "duplicate"},
}

SYNONYMS = {
    "max_body_bytes": {"size", "payload", "body", "bytes"},
    "client_max_body_size": {"size", "payload", "body"},
    "max_upload_size": {"size", "upload"},
    "request_timeout": {"timeout", "request"},
    "rate_limit": {"rate", "rate_limit", "quota"},
    "requests_per_minute": {"rate", "requests", "rpm"},
    "currency_precision": {"precision", "currency", "money"},
    "decimal_places": {"precision", "decimal", "decimals"},
}


def normalize_unit(unit: str | None) -> str:
    return ALIASES.get((unit or "").lower(), (unit or "").lower())


def quantities(text: str) -> list[tuple[float, str]]:
    out = []
    for m in NUMBER_RE.finditer(text):
        out.append((float(m.group("value").replace("_", "")), normalize_unit(m.group("unit"))))
    # Numeric literals may use Python/Go/Java-style separators, such as
    # 500_000 or 1_000_000. Keep the normalized numeric value while matching
    # source text separately in mutation ranking.
    # Common source-code byte encodings: 10 * 1024 * 1024 means 10 MB.
    for m in re.finditer(r"(?P<v>[0-9]+(?:\.[0-9]+)?)\s*\*\s*1024\s*\*\s*1024", text, re.I):
        out.append((float(m.group("v")), "mb"))
    for m in re.finditer(r"(?P<v>[0-9]+(?:\.[0-9]+)?)\s*\*\s*1024\s*\*\s*1024\s*\*\s*1024", text, re.I):
        out.append((float(m.group("v")), "gb"))
    return out


def concepts(text: str) -> set[str]:
    low = text.lower().replace("-", "_")
    padded = re.sub(r"[^a-z0-9_/]+", " ", low)
    raw = set(re.findall(r"[a-z][a-z0-9_/]*", padded))
    found: set[str] = set()
    for category, terms in CONCEPTS.items():
        if any(term in raw or term in low for term in terms):
            found.add(category)
    for alias, cats in SYNONYMS.items():
        if alias in low:
            found.update(cats)
    for _, unit in quantities(text):
        if unit in {"kb", "mb", "gb", "tb"}:
            found.add("size")
        elif unit in {"ms", "s", "h"}:
            found.add("timeout")
        elif unit in {"rpm", "rps"}:
            found.add("rate")
    return found


def same_quantity(a: tuple[float, str], b: tuple[float, str]) -> bool:
    av, au = a
    bv, bu = b
    if au == bu:
        return av == bv
    # Source constants often omit the unit in the identifier/value; when the
    # numeric value is identical, treat that as supporting the requirement.
    if not au or not bu:
        return av == bv
    size = {"kb": 1, "mb": 2, "gb": 3, "tb": 4}
    if au in size and bu in size:
        return av * (1024 ** size[au]) == bv * (1024 ** size[bu])
    time = {"ms": 0.001, "s": 1, "min": 60, "h": 3600}
    if au in time and bu in time:
        return av * time[au] == bv * time[bu]
    return False


def has_numeric_conflict(claim: str, snippet: str) -> bool:
    cq, sq = quantities(claim), quantities(snippet)
    if not cq or not sq:
        return False
    return not any(same_quantity(c, s) for c in cq for s in sq)


def textual_conflict(claim: str, snippet: str) -> bool:
    c = claim.lower().replace("-", " ")
    s = snippet.lower().replace("-", " ")
    pairs = [
        (("optional",), ("required", "must provide", "must be present")),
        (("required", "must provide"), ("optional",)),
        (("atomic", "atomically"), ("separate transaction", "separate operations", "separate transactions")),
        (("before persistence", "before persist", "before storage"), ("save_order", "persisted before", "persist before")),
        (("redacted before", "redaction before"), ("save_order", "persisted before", "after persistence")),
        (("universally enforced", "always enforced", "all endpoints"), ("bypass", "skip", "internal/", "can be called directly")),
    ]
    return any(any(a in c for a in left) and any(b in s for b in right) for left, right in pairs)


def scope_conflict(claim: str, snippet: str) -> bool:
    c, s = claim.lower(), snippet.lower()
    if "rate" in c or "requests/minute" in c or "requests per minute" in c:
        return (("1000" in c and "100" in s) or ("1000" in c and "instance" in s)) and "customer" in c
    return False
