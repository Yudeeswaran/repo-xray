from skills.xray.requirements import concepts, quantities, has_numeric_conflict

def test_units_preserve_mb_and_ms():
    assert (10.0, "mb") in quantities("10 MB")
    assert (30.0, "s") in quantities("30 seconds")
    assert (250.0, "ms") in quantities("250 ms")

def test_source_code_mb_encoding_is_normalized():
    assert (10.0, "mb") in quantities("MAX_BODY_BYTES = 10 * 1024 * 1024")

def test_concepts_map_common_requirement_domains():
    assert "size" in concepts("Maximum order payload is 25 MB")
    assert "timeout" in concepts("request timeout is 60 seconds")
    assert "rate" in concepts("1000 requests per minute")
    assert "precision" in concepts("currency uses 2 decimals")

def test_numeric_conflict_requires_domain_match_elsewhere():
    assert has_numeric_conflict("request timeout is 60 seconds", "REQUEST_TIMEOUT = 30")
