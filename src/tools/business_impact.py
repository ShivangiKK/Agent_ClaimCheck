"""
ClaimCheck Business Impact Engine

This module evaluates whether a statistically significant result is also
commercially meaningful.

Purpose:
- calculate expected value per customer/user/unit
- compare treatment economics against control economics
- identify whether broad rollout is financially justified
- support human-review routing when lift is positive but economics are negative
"""

from typing import Any, Dict, List, Optional

import pandas as pd


def calculate_business_impact(
    statistical_result: Dict[str, Any],
    business_value_per_success: float,
    intervention_cost_per_success: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate expected value impact for a binary outcome treatment/control result.

    Parameters
    ----------
    statistical_result:
        Output from run_two_proportion_test.
    business_value_per_success:
        Estimated value of one successful outcome.
        Example: revenue or contribution margin from one purchase.
    intervention_cost_per_success:
        Estimated cost associated with each treated success or intervention.
        Example: campaign incentive cost, discount cost, or fulfillment cost.

    Returns
    -------
    Dict containing:
    - control expected value per unit
    - treatment expected value per unit
    - incremental expected value per unit
    - total incremental expected value over treated population
    - financially_positive flag
    """
    if statistical_result.get("method") != "two_proportion_test":
        return {
            "business_impact_runnable": False,
            "reason": "Business impact calculation currently supports two_proportion_test outputs only.",
        }

    control_rate = statistical_result["control_rate"]
    treatment_rate = statistical_result["treatment_rate"]
    treatment_n = statistical_result["treatment_n"]

    control_expected_value_per_unit = control_rate * business_value_per_success

    treatment_expected_value_per_unit = (
        treatment_rate * business_value_per_success
    ) - (
        treatment_rate * intervention_cost_per_success
    )

    incremental_expected_value_per_unit = (
        treatment_expected_value_per_unit - control_expected_value_per_unit
    )

    total_incremental_expected_value = (
        incremental_expected_value_per_unit * treatment_n
    )

    return {
        "business_impact_runnable": True,
        "business_value_per_success": float(business_value_per_success),
        "intervention_cost_per_success": float(intervention_cost_per_success),
        "control_expected_value_per_unit": float(control_expected_value_per_unit),
        "treatment_expected_value_per_unit": float(treatment_expected_value_per_unit),
        "incremental_expected_value_per_unit": float(incremental_expected_value_per_unit),
        "total_incremental_expected_value": float(total_incremental_expected_value),
        "financially_positive": bool(incremental_expected_value_per_unit > 0),
        "business_interpretation": (
            "Treatment is financially positive under the provided assumptions."
            if incremental_expected_value_per_unit > 0
            else "Treatment is not financially positive under the provided assumptions."
        ),
    }


def calculate_segment_business_impact(
    segment_results: List[Dict[str, Any]],
    business_value_per_success: float,
    intervention_cost_per_success: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Calculate business impact for each segment result.

    Each segment result is expected to contain:
    - segment_col
    - segment_value
    - control_rate
    - treatment_rate
    - treatment_n
    - absolute_lift
    - p_value
    """
    enriched_segments = []

    for segment in segment_results:
        control_rate = segment.get("control_rate")
        treatment_rate = segment.get("treatment_rate")
        treatment_n = segment.get("treatment_n")

        if control_rate is None or treatment_rate is None or treatment_n is None:
            enriched = {
                **segment,
                "business_impact_runnable": False,
                "business_reason": "Missing control_rate, treatment_rate, or treatment_n.",
            }
            enriched_segments.append(enriched)
            continue

        control_expected_value_per_unit = control_rate * business_value_per_success

        treatment_expected_value_per_unit = (
            treatment_rate * business_value_per_success
        ) - (
            treatment_rate * intervention_cost_per_success
        )

        incremental_expected_value_per_unit = (
            treatment_expected_value_per_unit - control_expected_value_per_unit
        )

        total_incremental_expected_value = (
            incremental_expected_value_per_unit * treatment_n
        )

        enriched = {
            **segment,
            "business_impact_runnable": True,
            "business_value_per_success": float(business_value_per_success),
            "intervention_cost_per_success": float(intervention_cost_per_success),
            "control_expected_value_per_unit": float(control_expected_value_per_unit),
            "treatment_expected_value_per_unit": float(treatment_expected_value_per_unit),
            "incremental_expected_value_per_unit": float(incremental_expected_value_per_unit),
            "total_incremental_expected_value": float(total_incremental_expected_value),
            "financially_positive": bool(incremental_expected_value_per_unit > 0),
        }

        enriched_segments.append(enriched)

    return enriched_segments


def summarize_business_impact(
    business_impact: Dict[str, Any],
) -> str:
    """
    Create a concise human-readable summary of the business impact result.
    """
    if not business_impact.get("business_impact_runnable"):
        return business_impact.get(
            "reason",
            "Business impact calculation was not runnable.",
        )

    incremental_value = business_impact.get("incremental_expected_value_per_unit")
    total_value = business_impact.get("total_incremental_expected_value")
    financially_positive = business_impact.get("financially_positive")

    direction = "positive" if financially_positive else "negative"

    return (
        f"Business impact is {direction}. "
        f"Incremental expected value per unit is ${incremental_value:,.4f}. "
        f"Estimated total incremental value over the treated population is ${total_value:,.2f}."
    )


def identify_financially_positive_segments(
    enriched_segment_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Return only segments where treatment economics are financially positive.
    """
    return [
        segment for segment in enriched_segment_results
        if segment.get("business_impact_runnable")
        and segment.get("financially_positive")
    ]


def identify_strongest_business_segment(
    enriched_segment_results: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Identify the segment with the highest incremental expected value per unit.
    """
    runnable_segments = [
        segment for segment in enriched_segment_results
        if segment.get("business_impact_runnable")
        and segment.get("incremental_expected_value_per_unit") is not None
    ]

    if not runnable_segments:
        return None

    return max(
        runnable_segments,
        key=lambda segment: segment["incremental_expected_value_per_unit"],
    )
