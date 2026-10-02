from __future__ import annotations
from .budget import estimate
from .scope import count_files

def plan(root=".", claims=10, github_items=0, mutations=0, path_globs=("**/*",)):
    files = count_files(root, path_globs)
    b = estimate(claims, files, github_items, mutations)
    return {
        "mode": "adaptive",
        "estimated": b.to_dict(),
        "operations": [
            "deterministic repository discovery",
            "targeted Git history lookup",
            "scoped GitHub lookup when available",
            "targeted reasoning",
            "evidence validation",
        ],
        "confirmation_rule": "required for high estimated spend; small deterministic scans may proceed immediately",
    }
