from skills.xray.budget import estimate

def test_large_work_requires_confirmation():
    r=estimate(claims=100,files=1000,github_items=100,mutations=10)
    assert r.requires_confirmation
    assert r.high_tokens > r.low_tokens
