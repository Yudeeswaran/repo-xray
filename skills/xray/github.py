from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


class GitHubUnavailable(RuntimeError):
    """Raised when GitHub evidence cannot be collected safely."""


def gh_available() -> bool:
    try:
        p = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _git_remote(root: Path | str):
    try:
        p = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def repo_name(root: Path | str):
    remote = _git_remote(root)
    if not remote:
        return None
    # Supports https://github.com/o/r(.git), git@github.com:o/r(.git), and
    # ssh://git@github.com/o/r(.git). Ignore query/fragment noise.
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?(?:[?#].*)?$", remote.rstrip("/"))
    return m.group(1) if m else None


def _gh_result(args, root=None, timeout=20):
    if not gh_available():
        return None, "gh CLI is unavailable"
    try:
        p = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(root) if root else None,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, f"gh command timed out after {timeout}s"
    except OSError as exc:
        return None, f"unable to execute gh: {exc}"
    if p.returncode:
        detail = (p.stderr or p.stdout or "").strip().replace("\n", " ")
        return None, f"gh exited {p.returncode}: {detail[:500]}"
    try:
        return json.loads(p.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"gh returned invalid JSON: {exc}"


def _gh(args, root=None, timeout=20):
    data, _ = _gh_result(args, root, timeout=timeout)
    return data


def search_issues(root, query, limit=20):
    repo = repo_name(root)
    args = ["issue", "list"] + (["-R", repo] if repo else []) + [
        "--search", query, "--limit", str(max(1, min(limit, 100))),
        "--json", "number,title,state,url,body,author,createdAt,updatedAt,labels",
    ]
    return _gh(args, root) or []


def search_prs(root, query, limit=20):
    repo = repo_name(root)
    args = ["pr", "list"] + (["-R", repo] if repo else []) + [
        "--search", query, "--limit", str(max(1, min(limit, 100))),
        "--json", "number,title,state,url,body,author,createdAt,updatedAt,labels",
    ]
    return _gh(args, root) or []


def issue_view(root, number):
    repo = repo_name(root)
    args = ["issue", "view", str(number)] + (["-R", repo] if repo else []) + [
        "--json", "number,title,state,url,body,author,createdAt,updatedAt,comments,labels"
    ]
    return _gh(args, root)


def pr_view(root, number):
    repo = repo_name(root)
    args = ["pr", "view", str(number)] + (["-R", repo] if repo else []) + [
        "--json", "number,title,state,url,body,author,createdAt,updatedAt,comments,reviews,files,commits,labels"
    ]
    return _gh(args, root)


def _fixture_discussion(root, query, limit=20):
    fixture = Path(root) / "github-fixtures.json"
    if not fixture.exists():
        return None
    try:
        data = json.loads(fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_/.-]{3,}", query)]

    def match(item):
        hay = ((item.get("title") or "") + " " + (item.get("body") or "")).lower()
        return not terms or any(t in hay for t in terms)

    return {
        "repository": data.get("repository") or "fixture",
        "query": query,
        "issues": [x for x in data.get("issues", []) if match(x)][:limit],
        "pull_requests": [x for x in data.get("pull_requests", []) if match(x)][:limit],
        "fixture": True,
    }


def search_discussion(root, query, limit=20, hydrate=False):
    """Search issue/PR discussion with explicit source metadata.

    GitHub failures are surfaced in ``errors`` rather than being interpreted as
    evidence that no matching discussion exists. A local fixture is used only
    when the real GitHub client is unavailable or returned no matches.
    """
    root = Path(root)
    fixture = _fixture_discussion(root, query, limit)
    if not gh_available():
        if fixture is not None:
            return fixture | {"errors": ["gh CLI is unavailable; used local fixture"]}
        return {"repository": repo_name(root), "query": query, "issues": [],
                "pull_requests": [], "errors": ["gh CLI is unavailable"]}

    repo = repo_name(root)
    common = ["--search", query, "--limit", str(max(1, min(limit, 100))),
              "--json", "number,title,state,url,body,author,createdAt,updatedAt,labels"]
    errors = []
    issues, err = _gh_result(["issue", "list"] + (["-R", repo] if repo else []) + common, root)
    if err:
        errors.append(f"issues: {err}")
    prs, err = _gh_result(["pr", "list"] + (["-R", repo] if repo else []) + common, root)
    if err:
        errors.append(f"pull_requests: {err}")
    issues = issues or []
    prs = prs or []

    if not issues and not prs and not errors and fixture is not None:
        return fixture | {"errors": ["GitHub returned no matches; used local fixture"]}

    if hydrate:
        hydrated_issues = []
        for item in issues:
            hydrated = issue_view(root, item.get("number"))
            hydrated_issues.append(hydrated or item)
        hydrated_prs = []
        for item in prs:
            hydrated = pr_view(root, item.get("number"))
            hydrated_prs.append(hydrated or item)
        issues, prs = hydrated_issues, hydrated_prs

    return {"repository": repo, "query": query, "issues": issues,
            "pull_requests": prs, "errors": errors}
