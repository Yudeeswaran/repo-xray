from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class BudgetEstimate:
    files: int
    claims: int
    github_items: int
    mutations: int
    operations: int
    reasoning_calls: int
    low_tokens: int
    high_tokens: int
    requires_confirmation: bool

    def to_dict(self): return asdict(self)

def estimate(claims=10, files=500, github_items=0, mutations=0):
    claims = max(0, claims); files=max(0,files); github_items=max(0,github_items); mutations=max(0,mutations)
    reasoning_calls = max(1, (claims + 4)//5) + mutations*2 + (github_items+9)//10
    # Deliberately broad. Discovery itself is deterministic and not counted as LLM spend.
    low = reasoning_calls * 8_000
    high = reasoning_calls * 30_000
    operations = files + github_items + mutations
    return BudgetEstimate(files,claims,github_items,mutations,operations,reasoning_calls,low,high,high >= 150_000 or reasoning_calls >= 20)
