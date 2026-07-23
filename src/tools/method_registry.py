"""
ClaimCheck Method Registry

This module defines the approved analytical method families that ClaimCheck
can select from.

The registry separates:
- methods currently implemented in the prototype
- methods planned for future versions
- methods that require human review
"""

from typing import Any, Dict


METHOD_REGISTRY: Dict[str, Dict[str, Any]] = {
    "two_proportion_test": {
        "status": "implemented",
        "claim_types": ["causal_impact", "comparative", "prescriptive_recommendation"],
        "required_structure": [
            "binary_outcome",
            "binary_treatment",
            "two_groups",
        ],
        "description": "Tests whether a binary outcome differs between treatment and control groups.",
        "example": "Did the campaign increase purchase rate?",
        "human_review_required": False,
    },
    "two_sample_t_test": {
        "status": "implemented",
        "claim_types": ["causal_impact", "comparative", "prescriptive_recommendation"],
        "required_structure": [
            "numeric_outcome",
            "binary_treatment",
            "two_groups",
        ],
        "description": "Tests whether a numeric outcome differs between treatment and control groups.",
        "example": "Did the campaign increase average revenue?",
        "human_review_required": False,
    },
    "predictive_driver_review": {
        "status": "prototype_supported",
        "claim_types": ["predictive", "diagnostic"],
        "required_structure": [
            "target_variable",
            "features",
        ],
        "description": "Reviews whether a claim is predictive or diagnostic rather than causal.",
        "example": "Which factors predict churn?",
        "human_review_required": True,
    },
    "descriptive_only": {
        "status": "implemented",
        "claim_types": ["descriptive"],
        "required_structure": [
            "metric",
        ],
        "description": "Summarizes what happened without causal or predictive interpretation.",
        "example": "Revenue increased by 12% last month.",
        "human_review_required": False,
    },
    "pre_post_analysis": {
        "status": "planned",
        "claim_types": ["causal_impact", "comparative"],
        "required_structure": [
            "outcome",
            "time_period",
            "intervention_date",
        ],
        "description": "Compares outcomes before and after an intervention. Requires caution because pre/post designs alone are weak for causal inference.",
        "example": "Revenue increased after the product launch.",
        "human_review_required": True,
    },
    "difference_in_differences": {
        "status": "planned",
        "claim_types": ["causal_impact"],
        "required_structure": [
            "outcome",
            "treated_group",
            "control_group",
            "pre_period",
            "post_period",
        ],
        "description": "Estimates treatment effect using treated and control groups across pre/post periods.",
        "example": "Did the policy change reduce churn compared with unaffected customers?",
        "human_review_required": True,
    },
    "regression_adjusted_review": {
        "status": "planned",
        "claim_types": ["causal_impact", "predictive", "diagnostic"],
        "required_structure": [
            "outcome",
            "features",
            "model_specification",
        ],
        "description": "Uses regression or model-based adjustment to review relationships after controlling for covariates.",
        "example": "Did discount exposure affect purchase after controlling for income and prior usage?",
        "human_review_required": True,
    },
}


def get_method_registry() -> Dict[str, Dict[str, Any]]:
    """
    Return the approved ClaimCheck method registry.
    """
    return METHOD_REGISTRY


def get_method_info(method_name: str) -> Dict[str, Any]:
    """
    Return metadata for one method.
    """
    if method_name not in METHOD_REGISTRY:
        raise ValueError(f"Unknown method: {method_name}")

    return METHOD_REGISTRY[method_name]
