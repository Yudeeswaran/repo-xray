from pathlib import Path
from skills.xray.mutate import mutate, parse_change
ROOT=Path(__file__).parent/"fixtures"/"repo_mutation"

def test_parse_change():
    assert parse_change("10 MB -> 50 MB")=={"old":10.0,"old_unit":"mb","new":50.0,"new_unit":"mb"}

def test_mutation_finds_concrete_encodings():
    r=mutate(ROOT,"10 MB -> 50 MB")
    files={x["locator"]["file"] for x in r["matches"]}
    assert "server.py" in files
    assert "nginx.conf" in files
    assert r["parsed"]["new"]==50
    assert any(x["type"]=="config" for x in r["impacts"])

def test_parse_precision_change():
    assert parse_change("2 decimals -> 3 decimals")=={"old":2.0,"old_unit":"decimals","new":3.0,"new_unit":"decimals"}

def test_parse_rate_scope_change():
    assert parse_change("100/min -> 1000/min")=={"old":100.0,"old_unit":"rpm","new":1000.0,"new_unit":"rpm"}

def test_mutation_distinguishes_exact_values_from_semantic_candidates():
    r = mutate(ROOT, "10 MB -> 50 MB")
    assert any(x["match_kind"] == "direct_value" for x in r["matches"])
    assert all(0 <= x["confidence"] <= 1 for x in r["matches"])
    assert any(x["match_kind"] == "direct_value" for x in r["impacts"])

def test_mutation_matches_separator_encoded_numeric_literals(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "config.py").write_text('MAX_FORM_MEMORY_SIZE = 500_000\n', encoding='utf-8')
    r = mutate(root, "500000 bytes -> 1000000 bytes")
    assert any(x["match_kind"] == "direct_value" for x in r["matches"])

def test_mutation_deduplicates_history_patterns(tmp_path, monkeypatch):
    import skills.xray.mutate as m
    calls=[]
    monkeypatch.setattr(m, "search_history", lambda *args, **kwargs: calls.append(args[1]) or [])
    (tmp_path / "app.py").write_text("REQUEST_TIMEOUT = 30\n", encoding="utf-8")
    m.mutate(tmp_path, "30 seconds -> 60 seconds")
    assert len(calls) == len(set(calls))
