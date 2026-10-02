import json
from skills.xray.ci import check

def write(p, claims):
    p.write_text(json.dumps({"schema_version":"1.0","claims":claims}))

def c(cid,risk="HIGH",classification="CONTRADICTED"):
    return {"claim_id":cid,"classification":classification,"risk":risk}

def test_ci_fails_only_for_new_high_contradiction(tmp_path):
    baseline=tmp_path/"baseline.json"; current=tmp_path/"current.json"
    write(baseline,[c("C-old")]); write(current,[c("C-old"),c("C-new")])
    r=check(current,baseline)
    assert not r["ok"] and [x["claim_id"] for x in r["new_high_contradictions"]]==["C-new"]

def test_ci_passes_for_existing_finding(tmp_path):
    baseline=tmp_path/"baseline.json"; current=tmp_path/"current.json"
    write(baseline,[c("C-old")]); write(current,[c("C-old")])
    assert check(current,baseline)["ok"]
