from src.tools.language_guardrail import (
    scan_for_blocked_language,
    rewrite_claim_language,
    generate_allowed_language_guidance,
)


def test_scan_blocks_causal_language_for_suggestive_tier():
    result = scan_for_blocked_language(
        text="The campaign drove purchases and proves the strategy works.",
        evidence_tier="Suggestive",
    )

    assert result["scan_runnable"] is True
    assert result["language_safe"] is False
    assert "drove" in result["blocked_terms_found"]
    assert "proves" in result["blocked_terms_found"]


def test_scan_allows_safe_language_for_suggestive_tier():
    result = scan_for_blocked_language(
        text="The campaign is associated with higher purchases and requires further review.",
        evidence_tier="Suggestive",
    )

    assert result["scan_runnable"] is True
    assert result["language_safe"] is True


def test_rewrite_claim_language_replaces_blocked_terms():
    result = rewrite_claim_language(
        text="The campaign drove purchases and should roll out.",
        evidence_tier="Suggestive",
    )

    assert result["rewrite_runnable"] is True
    assert result["language_safe_before"] is False
    assert "drove" in result["blocked_terms_found"]
    assert "should roll out" in result["blocked_terms_found"]


def test_generate_allowed_language_guidance():
    result = generate_allowed_language_guidance("Causal")

    assert result["guidance_runnable"] is True
    assert result["evidence_tier"] == "Causal"
    assert "blocked_terms" in result
