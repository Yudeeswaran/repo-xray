from skills.xray.github import gh_available

def test_github_adapter_is_safe_when_gh_missing():
    assert isinstance(gh_available(), bool)

def test_github_fixture_fallback():
    from pathlib import Path
    from skills.xray.github import search_discussion
    root=Path(__file__).parent/"fixtures"/"repo_verified"
    # No fixture here: adapter must remain safe and return an empty result shape.
    r=search_discussion(root,"timeout",limit=2)
    assert {"repository","query","issues","pull_requests"}.issubset(r)
    assert isinstance(r.get("errors", []), list)

def test_repo_name_supports_https_and_ssh(monkeypatch):
    from skills.xray import github
    urls = [
        "https://github.com/pallets/flask.git",
        "git@github.com:pallets/flask.git",
        "ssh://git@github.com/pallets/flask.git",
    ]
    for url in urls:
        monkeypatch.setattr(github, "_git_remote", lambda root, url=url: url)
        assert github.repo_name(".") == "pallets/flask"


def test_search_discussion_surfaces_issue_and_pr_errors(monkeypatch, tmp_path):
    from skills.xray import github
    monkeypatch.setattr(github, "gh_available", lambda: True)
    calls = []
    def fake(args, root=None, timeout=20):
        calls.append(args)
        if args[:2] == ["issue", "list"]:
            return None, "auth failed"
        if args[:2] == ["pr", "list"]:
            return [{"number": 1, "title": "timeout", "body": ""}], None
        raise AssertionError(args)
    monkeypatch.setattr(github, "_gh_result", fake)
    monkeypatch.setattr(github, "repo_name", lambda root: "owner/repo")
    result = github.search_discussion(tmp_path, "timeout")
    assert result["issues"] == []
    assert result["pull_requests"][0]["number"] == 1
    assert any(e.startswith("issues:") for e in result["errors"])


def test_search_discussion_uses_fixture_when_gh_missing(tmp_path):
    from skills.xray import github
    (tmp_path / "github-fixtures.json").write_text(
        '{"repository":"owner/repo","issues":[{"number":7,"title":"timeout","body":"60s"}],"pull_requests":[]}',
        encoding="utf-8",
    )
    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(github, "gh_available", lambda: False)
        result = github.search_discussion(tmp_path, "timeout")
        assert result["fixture"] is True
        assert result["issues"][0]["number"] == 7
        assert result["errors"]
    finally:
        monkeypatch.undo()
