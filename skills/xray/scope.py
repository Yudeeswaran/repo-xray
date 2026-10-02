from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import fnmatch
import os

DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "target", ".tox", ".mypy_cache", ".pytest_cache", "__pycache__", ".idea", ".vscode",
}

@dataclass
class SearchScope:
    root: str
    paths: list[str]
    patterns: list[str]
    git_range: str | None = None
    github_scope: list[str] | None = None
    ignored_dirs: list[str] | None = None

    def to_dict(self):
        return asdict(self)

def _ignored(path: Path, root: Path, ignored_dirs: set[str]) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in ignored_dirs for part in rel.parts)

def files_in_scope(root: Path, path_globs: Iterable[str] = ("**/*",), ignored_dirs: Iterable[str] = DEFAULT_IGNORES, ignored_files: Iterable[str] = ()):
    ignored_file_names = set(ignored_files)
    root = Path(root).resolve()
    ignored = set(ignored_dirs)
    seen: set[Path] = set()
    for glob in path_globs:
        for p in root.glob(glob):
            if p.is_file() and p not in seen and p.name not in ignored_file_names and not _ignored(p, root, ignored):
                seen.add(p)
                yield p

def matching_lines(root: Path, patterns: Iterable[str], path_globs: Iterable[str] = ("**/*",), ignored_dirs: Iterable[str] = DEFAULT_IGNORES, max_bytes: int = 2_000_000, ignored_files: Iterable[str] = (".xray-ground-truth.json", "github-fixtures.json")):
    ignored_file_names = set(ignored_files)
    patterns = [p for p in patterns if p]
    for p in files_in_scope(root, path_globs, ignored_dirs, ignored_file_names):
        try:
            if p.stat().st_size > max_bytes:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(x.lower() in low for x in patterns):
                yield p, n, line

def count_files(root: Path, path_globs=("**/*",)) -> int:
    return sum(1 for _ in files_in_scope(root, path_globs))
