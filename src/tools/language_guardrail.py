"""
ClaimCheck Language Guardrail

This module prevents unsupported analytical language from appearing in
executive-facing outputs.

Purpose:
- block causal language when evidence is not causal
- block decision-ready language when business review is not approved
- rewrite unsafe claims into evidence-appropriate language
"""

from typing import Any, Dict, List


BANNED_LANGUAGE_RULES = {
    "Descriptive": {
        "blocked_terms": [
            "caused", "causes", "drove", "driven", "led to", "resulted in",
            "proves", "proved", "proven", "impact", "effect", "should roll out",
            "recommend rollout", "approve rollout"
        ],
        "allowed_positioning": "describe what happened without causal or action claims",
    },
    "Predictive": {
        "blocked_terms": [
            "caused", "causes", "drove", "driven", "led to", "resulted in",
            "proves", "proved", "proven", "should roll out", "approve rollout"
        ],
        "allowed_positioning": "describe predictive association or risk ranking",
    },
    "Suggestive": {
        "blocked_terms": [
            "caused", "causes", "causal", "drove", "driven", "led to",
            "resulted in", "proves", "proved", "proven", "should roll out",
            "approve rollout", "decision-ready"
        ],
        "allowed_positioning": "describe association or directional evidence",
    },
    "Causal": {
        "blocked_terms": [
            "should roll out", "approve rollout", "decision-ready",
            "guaranteed", "risk-free"
        ],
        "allowed_positioning": "describe causal evidence but avoid action approval unless business impact is positive",
    },
    "Decision-Ready": {
        "blocked_terms": [
            "guaranteed", "risk-free", "certain"
        ],
        "allowed_positioning": "recommend action with appropriate caveats",
    },
}


REWRITE_MAP = {
    "caused": "is associated with",
    "causes": "is associated with",
    "drove": "is associated with higher",
    "driven": "associated with",
    "led to": "is associated with",
    "resulted in": "is associated with",
    "proves": "provides evidence consistent with",
    "proved": "provided evidence consistent with",
    "proven": "supported by available evidence",
    "should roll out": "should be reviewed before rollout",
    "approve rollout": "review before rollout approval",
    "decision-ready": "requires review before decision",
    "guaranteed": "estimated",
    "risk-free": "subject to risk",
    "certain": "estimated",
}


def scan_for_blocked_language(
    text: str,
    evidence_tier: str,
) -> Dict[str, Any]:
    """
    Scan text for language not allowed under the evidence tier.
    """
    rules = BANNED_LANGUAGE_RULES.get(evidence_tier)

    if rules is None:
        return {
            "scan_runnable": False,
            "reason": f"Unknown evidence tier: {evidence_tier}",
        }

    text_lower = text.lower()

    blocked_terms_found = [
        term for term in rules["blocked_terms"]
        if term.lower() in text_lower
    ]

    return {
        "scan_runnable": True,
        "evidence_tier": evidence_tier,
        "blocked_terms_found": blocked_terms_found,
        "language_safe": len(blocked_terms_found) == 0,
        "allowed_positioning": rules["allowed_positioning"],
    }


def rewrite_claim_language(
    text: str,
    evidence_tier: str,
) -> Dict[str, Any]:
    """
    Rewrite unsafe claim language into evidence-appropriate wording.
    """
    scan_result = scan_for_blocked_language(text, evidence_tier)

    if not scan_result.get("scan_runnable"):
        return {
            "rewrite_runnable": False,
            "reason": scan_result.get("reason"),
        }

    rewritten = text

    for blocked_term in scan_result["blocked_terms_found"]:
        replacement = REWRITE_MAP.get(blocked_term, "requires further review")
        rewritten = rewritten.replace(blocked_term, replacement)
        rewritten = rewritten.replace(blocked_term.capitalize(), replacement.capitalize())

    return {
        "rewrite_runnable": True,
        "original_text": text,
        "rewritten_text": rewritten,
        "language_safe_before": scan_result["language_safe"],
        "blocked_terms_found": scan_result["blocked_terms_found"],
        "evidence_tier": evidence_tier,
        "allowed_positioning": scan_result["allowed_positioning"],
    }


def generate_allowed_language_guidance(evidence_tier: str) -> Dict[str, Any]:
    """
    Provide guidance for what language is allowed under the evidence tier.
    """
    rules = BANNED_LANGUAGE_RULES.get(evidence_tier)

    if rules is None:
        return {
            "guidance_runnable": False,
            "reason": f"Unknown evidence tier: {evidence_tier}",
        }

    return {
        "guidance_runnable": True,
        "evidence_tier": evidence_tier,
        "allowed_positioning": rules["allowed_positioning"],
        "blocked_terms": rules["blocked_terms"],
    }
