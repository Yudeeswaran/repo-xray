from pathlib import Path
from skills.xray.xray import scan
ROOT=Path(__file__).parent / "fixtures"

def test_verified():
    r=scan(ROOT/"repo_verified",["60"],claim="API timeout is 60 seconds")
    assert r["claims"][0]["classification"]=="VERIFIED"

def test_contradicted():
    r=scan(ROOT/"repo_contradiction",["timeout","60","30"],claim="API timeout is 60 seconds")
    assert r["claims"][0]["classification"]=="CONTRADICTED"
    assert any(e["polarity"]=="contradicts" for e in r["claims"][0]["evidence"])

def test_unverified_contains_scope():
    r=scan(ROOT/"repo_unverified",["timeout"],claim="API timeout is 60 seconds")
    c=r["claims"][0]
    assert c["classification"]=="UNVERIFIED"
    assert c["search_scope"]["paths"]
    assert c["search_scope"]["patterns"]==["timeout"]

def test_uncheckable_runtime_claim():
    r=scan(ROOT/"repo_uncheckable",["RPS","production"],claim="This service scales to 10000 RPS in production")
    assert r["claims"][0]["classification"]=="UNCHECKABLE"

def test_two_letter_units_detect_numeric_contradiction():
    r=scan(ROOT/"repo_size_contradiction",["MAX_BODY_BYTES","10 MB","25 MB"],claim="Maximum order payload is 25 MB")
    assert r["claims"][0]["classification"]=="CONTRADICTED"
    assert any(e["polarity"]=="contradicts" for e in r["claims"][0]["evidence"])

def test_github_errors_are_recorded_in_scope(monkeypatch, tmp_path):
    import skills.xray.xray as xray
    monkeypatch.setattr(xray, "search_discussion", lambda *a, **k: {"issues": [], "pull_requests": [], "errors": ["auth failed"]})
    monkeypatch.setattr(xray, "gh_available", lambda: True)
    result = xray.verify_claim(tmp_path, "timeout is 60 seconds", ["timeout", "60 seconds"], include_github=True)
    scope = result["claims"][0]["search_scope"]["github_scope"]
    assert scope["errors"] == ["auth failed"]
    assert "auth failed" in " ".join(result["claims"][0]["notes"])
