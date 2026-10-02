from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from skills.xray.xray import verify_claim
from skills.xray.mutate import mutate

ROOT = Path(__file__).resolve().parent
GT = json.loads((ROOT / "ground-truth.json").read_text())

results=[]
for case in GT["cases"]:
    repo=ROOT/case["repo"]
    ledger=verify_claim(repo,case["claim"],case["patterns"])
    claim=ledger["claims"][0]
    row={"repo":case["repo"],"classification":claim["classification"],"expected":case["expected"],"classification_pass":claim["classification"]==case["expected"]}
    if "mutation" in case:
        m=mutate(repo,case["mutation"])
        direct=any(x["match_kind"]=="direct_value" for x in m["matches"])
        row.update({"mutation":case["mutation"],"mutation_matches":len(m["matches"]),"mutation_risk":m["risk"],"direct_value":direct,"direct_value_pass":direct==case.get("expect_direct_value",False)})
    results.append(row)

summary={
    "cases":len(results),
    "classification_pass":sum(x["classification_pass"] for x in results),
    "mutation_direct_value_pass":sum(x.get("direct_value_pass",True) for x in results),
    "results":results,
}
print(json.dumps(summary,indent=2,sort_keys=True))
raise SystemExit(0 if summary["classification_pass"]==summary["cases"] and summary["mutation_direct_value_pass"]==sum("mutation" in c for c in GT["cases"]) else 1)
