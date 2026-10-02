from __future__ import annotations

from pathlib import Path
from .evidence import load_ledger
from .risk import RISK_ORDER

FAIL_LEVELS={"HIGH","CRITICAL"}

def new_high_contradictions(current_path, baseline_path=None):
    current=load_ledger(current_path)
    baseline=load_ledger(baseline_path) if baseline_path and Path(baseline_path).exists() else {"claims":[]}
    old={c.get("claim_id"):(c.get("classification"),c.get("risk")) for c in baseline.get("claims",[])}
    findings=[]
    for c in current.get("claims",[]):
        if c.get("classification") != "CONTRADICTED" or c.get("risk") not in FAIL_LEVELS:
            continue
        prior=old.get(c.get("claim_id"))
        if prior is None or prior[0] != "CONTRADICTED" or RISK_ORDER.get(prior[1],0) < RISK_ORDER.get(c.get("risk"),0):
            findings.append(c)
    return findings

def check(current_path, baseline_path=None):
    findings=new_high_contradictions(current_path,baseline_path)
    return {"ok":not findings,"new_high_contradictions":findings}
