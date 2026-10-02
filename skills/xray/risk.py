from __future__ import annotations

RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def rank_risk(claim: str, evidence: list[dict], classification: str, mutation=False) -> str:
    """Rank the operational risk of a claim using semantic impact signals.

    The score is intentionally evidence-oriented: classification contributes a
    baseline, while domain-specific impact signals can raise the floor. Some
    mismatches are intrinsically broad even when their numeric delta is small:
    request timeouts, rate-limit scope, and monetary precision can affect many
    components or correctness boundaries.
    """
    text = (claim + " " + " ".join(str(e) for e in evidence)).lower()
    score = 0

    if classification == "CONTRADICTED":
        score += 3
    elif classification == "UNCHECKABLE":
        score += 0

    security = _contains_any(
        text,
        ("security", "auth", "permission", "credential", "secret", "encryption", "token"),
    )
    production_data = _contains_any(
        text,
        ("production", "database", "data loss", "payment", "memory", "outage", "migration"),
    )
    operational = _contains_any(
        text,
        ("timeout", "rate limit", "upload", "size", "capacity", "queue"),
    )

    if security:
        score += 3
    if production_data:
        score += 2
    if operational:
        score += 1
    if mutation:
        score += 2

    # Semantic impact floors. These are not numeric-delta rules: the same
    # absolute change can have very different consequences depending on the
    # boundary it changes.
    high_impact = False

    # Request/gateway/client timeout mismatches can alter cross-component
    # failure behavior, retries, queueing, and user-visible availability.
    if _contains_any(text, ("timeout", "request deadline", "deadline")):
        high_impact = True

    # Rate-limit contradictions can change tenant/customer isolation and
    # capacity guarantees, especially when the documented and runtime scopes
    # differ (e.g. customer vs instance).
    if _contains_any(text, ("rate limit", "rate-limit", "requests/minute", "requests per minute")):
        high_impact = True
    if _contains_any(text, ("upload", "payload", "max body", "body bytes", "size limit")) and mutation:
        high_impact = True

    # Queue visibility changes alter retry/lease behavior and can create
    # duplicate work even when the numeric delta looks modest.
    if _contains_any(text, ("visibility timeout", "queue visibility", "lease")):
        high_impact = True

    if _contains_any(text, ("rate limit", "rate-limit", "requests/minute", "requests per minute")):
        high_impact = True

    if _contains_any(text, ("idempotency", "duplicate charge", "payment retry", "payment retries", "pii", "redaction", "inventory reservation", "atomic inventory")):
        high_impact = True

    # Monetary precision is a financial-correctness boundary. Treat claims
    # involving currency precision, rounding, minor units, amounts, or money
    # representation as high impact when contradicted.
    money_terms = (
        "currency precision",
        "money precision",
        "decimal precision",
        "fractional minor",
        "minor units",
        "rounding",
        "currency",
    )
    if _contains_any(text, money_terms) and _contains_any(
        text, ("precision", "decimal", "round", "minor", "amount", "money", "currency")
    ):
        high_impact = True

    if high_impact and (classification == "CONTRADICTED" or mutation):
        score = max(score, 4)  # HIGH floor

    if score >= 7:
        return "CRITICAL"
    if score >= 4:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"
