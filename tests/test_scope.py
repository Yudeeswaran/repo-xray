from pathlib import Path
from skills.xray.scope import matching_lines

def test_scope_excludes_git(tmp_path):
    (tmp_path/"a.py").write_text("timeout=60\n")
    (tmp_path/".git").mkdir()
    (tmp_path/".git"/"x").write_text("timeout=999\n")
    hits=list(matching_lines(tmp_path,["timeout"]))
    assert len(hits)==1
