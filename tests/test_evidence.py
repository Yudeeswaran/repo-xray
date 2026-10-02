from skills.xray.evidence import make_claim

def test_claim_validation():
    c=make_claim("x","VERIFIED",[],{"paths":["**/*"],"patterns":["x"]},"LOW",0.8)
    assert c.claim_id.startswith("C-") and c.confidence==0.8

def test_evidence_rejects_invalid_confidence():
    from skills.xray.evidence import Evidence
    import pytest
    with pytest.raises(ValueError):
        Evidence("repository", {}, confidence=1.1)
