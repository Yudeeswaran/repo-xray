from skills.xray.planner import plan

def test_planner_counts_files(tmp_path):
    (tmp_path/"a.py").write_text("x")
    r=plan(tmp_path,claims=10)
    assert r["estimated"]["files"]==1
    assert "low_tokens" in r["estimated"]

def test_plan_exposes_adaptive_estimate_and_confirmation():
    from skills.xray.planner import plan
    r=plan(".", claims=15, github_items=8, mutations=2)
    assert r["mode"]=="adaptive"
    assert r["estimated"]["requires_confirmation"] is True
    assert r["estimated"]["low_tokens"] <= r["estimated"]["high_tokens"]
