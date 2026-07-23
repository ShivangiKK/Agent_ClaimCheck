"""
ClaimCheck Method Selector

This module selects an analytical method family based on the user claim,
dataset profile, and configuration.

It represents the deterministic part of Fisher, the Method Selection Agent.
"""

from typing import Any, Dict, List, Optional

from src.tools.method_registry import get_method_info


CAUSAL_TERMS = [
    "caused",
    "cause",
    "causal",
    "drove",
    "driven",
    "led to",
    "resulted in",
    "increased because",
    "decreased because",
    "impact",
    "effect",
]

PRESCRIPTIVE_TERMS = [
    "should",
    "recommend",
    "roll out",
    "rollout",
    "scale",
    "approve",
    "launch",
    "target",
    "invest",
    "continue",
    "stop",
]

PREDICTIVE_TERMS = [
    "predict",
    "forecast",
    "likely",
    "risk",
    "propensity",
    "score",
]

DESCRIPTIVE_TERMS = [
    "increased",
    "decreased",
    "changed",
    "grew",
    "declined",
    "was",
    "were",
]


def infer_claim_intent(claim: str) -> Dict[str, Any]:
    """
    Infer the user's requested claim intent from text.

    This is intentionally simple in the prototype. In the CrewAI version,
    Toulmin will improve this with structured LLM claim framing.
    """
    claim_lower = claim.lower()

    detected_intents: List[str] = []

    if any(term in claim_lower for term in PRESCRIPTIVE_TERMS):
        detected_intents.append("prescriptive_recommendation")

    if any(term in claim_lower for term in CAUSAL_TERMS):
        detected_intents.append("causal_impact")

    if any(term in claim_lower for term in PREDICTIVE_TERMS):
        detected_intents.append("predictive")

    if not detected_intents and any(term in claim_lower for term in DESCRIPTIVE_TERMS):
        detected_intents.append("descriptive")

    if not detected_intents:
        detected_intents.append("unknown")

    primary_intent = detected_intents[0]

    return {
        "primary_intent": primary_intent,
        "detected_intents": detected_intents,
    }


def _is_binary_column(profile: Dict[str, Any], column_name: Optional[str]) -> bool:
    """
    Check whether a configured column is detected as binary.
    """
    if column_name is None:
        return False

    binary_columns = profile.get("role_summary", {}).get("binary_columns", [])
    return column_name in binary_columns


def _is_numeric_column(profile: Dict[str, Any], column_name: Optional[str]) -> bool:
    """
    Check whether a configured column is detected as numeric.
    """
    if column_name is None:
        return False

    numeric_columns = profile.get("role_summary", {}).get("numeric_columns", [])
    return column_name in numeric_columns


def select_method(
    claim: str,
    profile: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Select the appropriate analytical method family.

    Parameters
    ----------
    claim:
        User-submitted business claim.
    profile:
        Output from profile_dataset.
    config:
        User or app-provided configuration.

    Returns
    -------
    Dict containing:
    - selected_method
    - method_status
    - auto_runnable
    - human_review_required
    - reason
    - claim_intent
    """
    claim_intent = infer_claim_intent(claim)

    outcome_col = config.get("outcome_col")
    treatment_col = config.get("treatment_col")
    time_col = config.get("time_col")

    has_outcome = outcome_col in profile.get("columns", [])
    has_treatment = treatment_col in profile.get("columns", [])
    has_time = time_col in profile.get("columns", []) if time_col else False

    outcome_is_binary = _is_binary_column(profile, outcome_col)
    outcome_is_numeric = _is_numeric_column(profile, outcome_col)
    treatment_is_binary = _is_binary_column(profile, treatment_col)

    if has_outcome and has_treatment and outcome_is_binary and treatment_is_binary:
        method_name = "two_proportion_test"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Binary outcome and binary treatment detected. Two-proportion test is appropriate.",
            "claim_intent": claim_intent,
        }

    if has_outcome and has_treatment and outcome_is_numeric and treatment_is_binary:
        method_name = "two_sample_t_test"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Numeric outcome and binary treatment detected. Two-sample t-test is appropriate.",
            "claim_intent": claim_intent,
        }

    if has_outcome and has_time and not has_treatment:
        method_name = "pre_post_analysis"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": False,
            "human_review_required": True,
            "reason": "Outcome and time field detected, but no treatment/control structure. Pre/post review requires caution and human review.",
            "claim_intent": claim_intent,
        }

    if claim_intent["primary_intent"] == "predictive":
        method_name = "predictive_driver_review"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": False,
            "human_review_required": True,
            "reason": "Claim appears predictive. Prototype routes predictive review to human-assisted analysis.",
            "claim_intent": claim_intent,
        }

    if claim_intent["primary_intent"] == "descriptive":
        method_name = "descriptive_only"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Claim appears descriptive and does not require causal interpretation.",
            "claim_intent": claim_intent,
        }

    return {
        "selected_method": "human_review",
        "method_status": "unsupported",
        "auto_runnable": False,
        "human_review_required": True,
        "reason": "No approved method could be safely selected from the available dataset structure and claim.",
        "claim_intent": claim_intent,
    }"""
ClaimCheck Method Selector

This module selects an analytical method family based on the user claim,
dataset profile, and configuration.

It represents the deterministic part of Fisher, the Method Selection Agent.
"""

from typing import Any, Dict, List, Optional

from src.tools.method_registry import get_method_info


CAUSAL_TERMS = [
    "caused",
    "cause",
    "causal",
    "drove",
    "driven",
    "led to",
    "resulted in",
    "increased because",
    "decreased because",
    "impact",
    "effect",
]

PRESCRIPTIVE_TERMS = [
    "should",
    "recommend",
    "roll out",
    "rollout",
    "scale",
    "approve",
    "launch",
    "target",
    "invest",
    "continue",
    "stop",
]

PREDICTIVE_TERMS = [
    "predict",
    "forecast",
    "likely",
    "risk",
    "propensity",
    "score",
]

DESCRIPTIVE_TERMS = [
    "increased",
    "decreased",
    "changed",
    "grew",
    "declined",
    "was",
    "were",
]


def infer_claim_intent(claim: str) -> Dict[str, Any]:
    """
    Infer the user's requested claim intent from text.

    This is intentionally simple in the prototype. In the CrewAI version,
    Toulmin will improve this with structured LLM claim framing.
    """
    claim_lower = claim.lower()

    detected_intents: List[str] = []

    if any(term in claim_lower for term in PRESCRIPTIVE_TERMS):
        detected_intents.append("prescriptive_recommendation")

    if any(term in claim_lower for term in CAUSAL_TERMS):
        detected_intents.append("causal_impact")

    if any(term in claim_lower for term in PREDICTIVE_TERMS):
        detected_intents.append("predictive")

    if not detected_intents and any(term in claim_lower for term in DESCRIPTIVE_TERMS):
        detected_intents.append("descriptive")

    if not detected_intents:
        detected_intents.append("unknown")

    primary_intent = detected_intents[0]

    return {
        "primary_intent": primary_intent,
        "detected_intents": detected_intents,
    }


def _is_binary_column(profile: Dict[str, Any], column_name: Optional[str]) -> bool:
    """
    Check whether a configured column is detected as binary.
    """
    if column_name is None:
        return False

    binary_columns = profile.get("role_summary", {}).get("binary_columns", [])
    return column_name in binary_columns


def _is_numeric_column(profile: Dict[str, Any], column_name: Optional[str]) -> bool:
    """
    Check whether a configured column is detected as numeric.
    """
    if column_name is None:
        return False

    numeric_columns = profile.get("role_summary", {}).get("numeric_columns", [])
    return column_name in numeric_columns


def select_method(
    claim: str,
    profile: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Select the appropriate analytical method family.

    Parameters
    ----------
    claim:
        User-submitted business claim.
    profile:
        Output from profile_dataset.
    config:
        User or app-provided configuration.

    Returns
    -------
    Dict containing:
    - selected_method
    - method_status
    - auto_runnable
    - human_review_required
    - reason
    - claim_intent
    """
    claim_intent = infer_claim_intent(claim)

    outcome_col = config.get("outcome_col")
    treatment_col = config.get("treatment_col")
    time_col = config.get("time_col")

    has_outcome = outcome_col in profile.get("columns", [])
    has_treatment = treatment_col in profile.get("columns", [])
    has_time = time_col in profile.get("columns", []) if time_col else False

    outcome_is_binary = _is_binary_column(profile, outcome_col)
    outcome_is_numeric = _is_numeric_column(profile, outcome_col)
    treatment_is_binary = _is_binary_column(profile, treatment_col)

    if has_outcome and has_treatment and outcome_is_binary and treatment_is_binary:
        method_name = "two_proportion_test"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Binary outcome and binary treatment detected. Two-proportion test is appropriate.",
            "claim_intent": claim_intent,
        }

    if has_outcome and has_treatment and outcome_is_numeric and treatment_is_binary:
        method_name = "two_sample_t_test"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Numeric outcome and binary treatment detected. Two-sample t-test is appropriate.",
            "claim_intent": claim_intent,
        }

    if has_outcome and has_time and not has_treatment:
        method_name = "pre_post_analysis"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": False,
            "human_review_required": True,
            "reason": "Outcome and time field detected, but no treatment/control structure. Pre/post review requires caution and human review.",
            "claim_intent": claim_intent,
        }

    if claim_intent["primary_intent"] == "predictive":
        method_name = "predictive_driver_review"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": False,
            "human_review_required": True,
            "reason": "Claim appears predictive. Prototype routes predictive review to human-assisted analysis.",
            "claim_intent": claim_intent,
        }

    if claim_intent["primary_intent"] == "descriptive":
        method_name = "descriptive_only"
        method_info = get_method_info(method_name)
        return {
            "selected_method": method_name,
            "method_status": method_info["status"],
            "auto_runnable": True,
            "human_review_required": False,
            "reason": "Claim appears descriptive and does not require causal interpretation.",
            "claim_intent": claim_intent,
        }

    return {
        "selected_method": "human_review",
        "method_status": "unsupported",
        "auto_runnable": False,
        "human_review_required": True,
        "reason": "No approved method could be safely selected from the available dataset structure and claim.",
        "claim_intent": claim_intent,
    }
