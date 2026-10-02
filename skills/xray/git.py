from __future__ import annotations

import subprocess
from pathlib import Path

class GitError(RuntimeError):
    pass

def run_git(root, *args, check=False, timeout=20):
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git command timed out after {timeout}s: git -C {root} {" ".join(args)}") from exc
    if check and p.returncode:
        raise GitError(p.stderr.strip() or "git command failed")
    return p.returncode, p.stdout, p.stderr

def is_repo(root) -> bool:
    code, _, _ = run_git(root, "rev-parse", "--is-inside-work-tree")
    return code == 0

def current_ref(root):
    code, out, _ = run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return out.strip() if code == 0 else None

def head(root):
    code, out, _ = run_git(root, "rev-parse", "HEAD")
    return out.strip() if code == 0 else None

def log(root, limit=50, path=None):
    args = ["log", f"-{limit}", "--date=iso-strict", "--format=%H%x09%ad%x09%an%x09%s"]
    if path:
        args += ["--", str(path)]
    code, out, _ = run_git(root, *args)
    if code:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) == 4:
            rows.append(dict(zip(("commit", "date", "author", "message"), parts)))
    return rows

def blame(root, path, line):
    code, out, err = run_git(root, "blame", "-L", f"{line},{line}", "--porcelain", "--", str(path))
    if code:
        return {"error": err.strip()}
    first = out.splitlines()[0].split() if out else []
    return {"commit": first[0] if first else None, "raw": out}

def search_history(root, pattern, limit=30):
    code, out, _ = run_git(root, "log", f"-{limit}", "-G", pattern, "--date=iso-strict", "--format=%H%x09%ad%x09%an%x09%s", timeout=15)
    if code:
        return []
    rows=[]
    for line in out.splitlines():
        parts=line.split("\t",3)
        if len(parts)==4:
            rows.append(dict(zip(("commit","date","author","message"),parts)))
    return rows

def diff_between(root, rev_range):
    code, out, err = run_git(root, "diff", "--unified=0", rev_range)
    return out if code == 0 else err

def changed_files(root, rev_range):
    code, out, _ = run_git(root, "diff", "--name-only", rev_range)
    return out.splitlines() if code == 0 else []
