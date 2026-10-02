from skills.xray.git import log

def test_git_log_returns_list(tmp_path):
    assert isinstance(log(tmp_path),list)

def test_run_git_timeout(monkeypatch, tmp_path):
    import subprocess
    from skills.xray.git import run_git, GitError
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=kwargs.get("timeout"))
    monkeypatch.setattr(subprocess, "run", fake_run)
    try:
        run_git(tmp_path, "status", timeout=1)
        assert False, "expected GitError"
    except GitError as exc:
        assert "timed out" in str(exc)
