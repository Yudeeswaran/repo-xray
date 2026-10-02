from skills.xray.risk import rank_risk


def test_contradiction_security_is_high():
    assert rank_risk("authentication secret contradiction", [], "CONTRADICTED") in {"HIGH", "CRITICAL"}


def test_request_timeout_contradiction_is_high():
    assert rank_risk(
        "60 second request timeout vs 30 second runtime timeout",
        [{"source": "gateway config", "value": "30s"}],
        "CONTRADICTED",
    ) == "HIGH"


def test_rate_limit_contradiction_is_high():
    assert rank_risk(
        "1000 requests/minute customer limit vs 100 requests/minute instance limit",
        [{"source": "helm", "value": "1000/min"}, {"source": "runtime", "value": "100/min"}],
        "CONTRADICTED",
    ) == "HIGH"


def test_currency_precision_contradiction_is_high():
    assert rank_risk(
        "currency precision documented as 2 decimals but storage uses fractional minor units",
        [{"source": "storage/money.py", "value": "* 1000"}],
        "CONTRADICTED",
    ) == "HIGH"


def test_local_non_production_contradiction_can_remain_medium():
    assert rank_risk(
        "README says the example port is 8080 but the local example uses 8081",
        [{"source": "README.md"}],
        "CONTRADICTED",
    ) == "MEDIUM"
