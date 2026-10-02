from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Any

CLASSIFICATIONS = {"VERIFIED", "CONTRADICTED", "UNVERIFIED", "UNCHECKABLE"}
RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
POLARITIES = {"supports", "contradicts", "context"}
STRENGTHS = {"direct", "test", "config", "history", "discussion", "inferred"}

@dataclass(frozen=True)
class Evidence:
    source_type: str
    locator: dict[str, Any]
    snippet: str = ""
    strength: str = "direct"
    polarity: str = "supports"
    confidence: float = 1.0

    def __post_init__(self):
        if self.polarity not in POLARITIES:
            raise ValueError(f"invalid polarity: {self.polarity}")
        if self.strength not in STRENGTHS:
            raise ValueError(f"invalid strength: {self.strength}")
        if not 0 <= self.confidence <= 1:
            raise ValueError("evidence confidence must be between 0 and 1")

@dataclass
class Claim:
    claim_id: str
    claim: str
    classification: str
    evidence: list[dict[str, Any]]
    search_scope: dict[str, Any]
    risk: str
    confidence: float
    notes: list[str] = field(default_factory=list)
    related_claims: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"invalid classification: {self.classification}")
        if self.risk not in RISKS:
            raise ValueError(f"invalid risk: {self.risk}")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self):
        return asdict(self)

def claim_id(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    return "C-" + hashlib.sha256(normalized.encode()).hexdigest()[:12]

def make_claim(text, classification, evidence, scope, risk="LOW", confidence=0.0, notes=None, related_claims=None):
    return Claim(claim_id(text), text.strip(), classification, evidence, scope, risk, confidence, notes or [], related_claims or [])

def new_ledger(root, claims, metadata=None):
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(Path(root).resolve()),
        "metadata": metadata or {},
        "claims": [c.to_dict() if isinstance(c, Claim) else c for c in claims],
    }

def save_ledger(ledger, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")

def load_ledger(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
