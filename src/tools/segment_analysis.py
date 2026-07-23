"""
ClaimCheck Segment Analysis Tool

This module checks whether treatment effects differ across user-defined segments.

Purpose:
- identify heterogeneous treatment effects
- find strongest and weakest segments
- support targeted review instead of broad rollout
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from src.tools.stats_engine import run_two_proportion_test


def run_segment_effects(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    segment_cols: Optional[List[str]] = None,
    alpha: float = 0.05,
    min_segment_size: int = 30,
) -> List[Dict[str, Any]]:
    """
    Run two-proportion tests within each configured segment.

    Each segment result includes treatment/control rates, lift, p-value,
    significance status, and sample sizes.
    """
    segment_cols = segment_cols or []
    results = []

    for segment_col in segment_cols:
        if segment_col not in df.columns:
            results.append({
                "segment_col": segment_col,
                "segment_value": None,
                "segment_label": None,
                "segment_runnable": False,
                "reason": "Segment column not found in dataset.",
            })
            continue

        for segment_value in sorted(df[segment_col].dropna().unique().tolist()):
            segment_df = df[df[segment_col] == segment_value]

            if len(segment_df) < min_segment_size:
                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": False,
                    "reason": "Segment size below minimum threshold.",
                    "segment_n": int(len(segment_df)),
                })
                continue

            try:
                stat_result = run_two_proportion_test(
                    df=segment_df,
                    outcome_col=outcome_col,
                    treatment_col=treatment_col,
                    alpha=alpha,
                )

                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": True,
                    "segment_n": int(len(segment_df)),
                    "control_n": stat_result["control_n"],
                    "treatment_n": stat_result["treatment_n"],
                    "control_rate": stat_result["control_rate"],
                    "treatment_rate": stat_result["treatment_rate"],
                    "absolute_lift": stat_result["absolute_lift"],
                    "absolute_lift_percentage_points": stat_result["absolute_lift_percentage_points"],
                    "p_value": stat_result["p_value"],
                    "statistically_significant": stat_result["statistically_significant"],
                })

            except Exception as error:
                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": False,
                    "reason": str(error),
                    "segment_n": int(len(segment_df)),
                })

    return results


def run_intersectional_segment_effects(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    segment_cols: Optional[List[str]] = None,
    alpha: float = 0.05,
    min_segment_size: int = 30,
) -> List[Dict[str, Any]]:
    """
    Run segment analysis across combinations of segment columns.

    Example:
    gender + gamer -> Female Gamer, Male Non-gamer, etc.
    """
    segment_cols = segment_cols or []

    if len(segment_cols) < 2:
        return []

    missing_cols = [col for col in segment_cols if col not in df.columns]
    if missing_cols:
        return [{
            "segment_col": "+".join(segment_cols),
            "segment_value": None,
            "segment_label": None,
            "segment_runnable": False,
            "reason": f"Missing segment columns: {missing_cols}",
        }]

    results = []

    grouped = df.groupby(segment_cols, dropna=True)

    for segment_values, segment_df in grouped:
        if not isinstance(segment_values, tuple):
            segment_values = (segment_values,)

        segment_label = " + ".join(
            f"{col}={val}" for col, val in zip(segment_cols, segment_values)
        )

        if len(segment_df) < min_segment_size:
            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": False,
                "reason": "Segment size below minimum threshold.",
                "segment_n": int(len(segment_df)),
            })
            continue

        try:
            stat_result = run_two_proportion_test(
                df=segment_df,
                outcome_col=outcome_col,
                treatment_col=treatment_col,
                alpha=alpha,
            )

            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": True,
                "segment_n": int(len(segment_df)),
                "control_n": stat_result["control_n"],
                "treatment_n": stat_result["treatment_n"],
                "control_rate": stat_result["control_rate"],
                "treatment_rate": stat_result["treatment_rate"],
                "absolute_lift": stat_result["absolute_lift"],
                "absolute_lift_percentage_points": stat_result["absolute_lift_percentage_points"],
                "p_value": stat_result["p_value"],
                "statistically_significant": stat_result["statistically_significant"],
            })

        except Exception as error:
            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": False,
                "reason": str(error),
                "segment_n": int(len(segment_df)),
            })

    return results


def summarize_segment_results(
    segment_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Summarize segment results for executive review.
    """
    runnable_segments = [
        segment for segment in segment_results
        if segment.get("segment_runnable")
    ]

    if not runnable_segments:
        return {
            "segments_evaluated": 0,
            "strongest_lift_segment": None,
            "weakest_lift_segment": None,
            "significant_segments": [],
            "summary": "No runnable segment results were available.",
        }

    strongest = max(
        runnable_segments,
        key=lambda segment: segment["absolute_lift"],
    )

    weakest = min(
        runnable_segments,
        key=lambda segment: segment["absolute_lift"],
    )

    significant_segments = [
        segment for segment in runnable_segments
        if segment.get("statistically_significant")
    ]

    return {
        "segments_evaluated": len(runnable_segments),
        "strongest_lift_segment": strongest,
        "weakest_lift_segment": weakest,
        "significant_segments": significant_segments,
        "summary": (
            f"{len(runnable_segments)} segments evaluated. "
            f"Strongest lift: {strongest['segment_label']} "
            f"({strongest['absolute_lift_percentage_points']:.2f} pp). "
            f"Weakest lift: {weakest['segment_label']} "
            f"({weakest['absolute_lift_percentage_points']:.2f} pp)."
        ),
    }"""
ClaimCheck Segment Analysis Tool

This module checks whether treatment effects differ across user-defined segments.

Purpose:
- identify heterogeneous treatment effects
- find strongest and weakest segments
- support targeted review instead of broad rollout
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from src.tools.stats_engine import run_two_proportion_test


def run_segment_effects(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    segment_cols: Optional[List[str]] = None,
    alpha: float = 0.05,
    min_segment_size: int = 30,
) -> List[Dict[str, Any]]:
    """
    Run two-proportion tests within each configured segment.

    Each segment result includes treatment/control rates, lift, p-value,
    significance status, and sample sizes.
    """
    segment_cols = segment_cols or []
    results = []

    for segment_col in segment_cols:
        if segment_col not in df.columns:
            results.append({
                "segment_col": segment_col,
                "segment_value": None,
                "segment_label": None,
                "segment_runnable": False,
                "reason": "Segment column not found in dataset.",
            })
            continue

        for segment_value in sorted(df[segment_col].dropna().unique().tolist()):
            segment_df = df[df[segment_col] == segment_value]

            if len(segment_df) < min_segment_size:
                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": False,
                    "reason": "Segment size below minimum threshold.",
                    "segment_n": int(len(segment_df)),
                })
                continue

            try:
                stat_result = run_two_proportion_test(
                    df=segment_df,
                    outcome_col=outcome_col,
                    treatment_col=treatment_col,
                    alpha=alpha,
                )

                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": True,
                    "segment_n": int(len(segment_df)),
                    "control_n": stat_result["control_n"],
                    "treatment_n": stat_result["treatment_n"],
                    "control_rate": stat_result["control_rate"],
                    "treatment_rate": stat_result["treatment_rate"],
                    "absolute_lift": stat_result["absolute_lift"],
                    "absolute_lift_percentage_points": stat_result["absolute_lift_percentage_points"],
                    "p_value": stat_result["p_value"],
                    "statistically_significant": stat_result["statistically_significant"],
                })

            except Exception as error:
                results.append({
                    "segment_col": segment_col,
                    "segment_value": segment_value,
                    "segment_label": f"{segment_col}={segment_value}",
                    "segment_runnable": False,
                    "reason": str(error),
                    "segment_n": int(len(segment_df)),
                })

    return results


def run_intersectional_segment_effects(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    segment_cols: Optional[List[str]] = None,
    alpha: float = 0.05,
    min_segment_size: int = 30,
) -> List[Dict[str, Any]]:
    """
    Run segment analysis across combinations of segment columns.

    Example:
    gender + gamer -> Female Gamer, Male Non-gamer, etc.
    """
    segment_cols = segment_cols or []

    if len(segment_cols) < 2:
        return []

    missing_cols = [col for col in segment_cols if col not in df.columns]
    if missing_cols:
        return [{
            "segment_col": "+".join(segment_cols),
            "segment_value": None,
            "segment_label": None,
            "segment_runnable": False,
            "reason": f"Missing segment columns: {missing_cols}",
        }]

    results = []

    grouped = df.groupby(segment_cols, dropna=True)

    for segment_values, segment_df in grouped:
        if not isinstance(segment_values, tuple):
            segment_values = (segment_values,)

        segment_label = " + ".join(
            f"{col}={val}" for col, val in zip(segment_cols, segment_values)
        )

        if len(segment_df) < min_segment_size:
            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": False,
                "reason": "Segment size below minimum threshold.",
                "segment_n": int(len(segment_df)),
            })
            continue

        try:
            stat_result = run_two_proportion_test(
                df=segment_df,
                outcome_col=outcome_col,
                treatment_col=treatment_col,
                alpha=alpha,
            )

            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": True,
                "segment_n": int(len(segment_df)),
                "control_n": stat_result["control_n"],
                "treatment_n": stat_result["treatment_n"],
                "control_rate": stat_result["control_rate"],
                "treatment_rate": stat_result["treatment_rate"],
                "absolute_lift": stat_result["absolute_lift"],
                "absolute_lift_percentage_points": stat_result["absolute_lift_percentage_points"],
                "p_value": stat_result["p_value"],
                "statistically_significant": stat_result["statistically_significant"],
            })

        except Exception as error:
            results.append({
                "segment_col": "+".join(segment_cols),
                "segment_value": segment_values,
                "segment_label": segment_label,
                "segment_runnable": False,
                "reason": str(error),
                "segment_n": int(len(segment_df)),
            })

    return results


def summarize_segment_results(
    segment_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Summarize segment results for executive review.
    """
    runnable_segments = [
        segment for segment in segment_results
        if segment.get("segment_runnable")
    ]

    if not runnable_segments:
        return {
            "segments_evaluated": 0,
            "strongest_lift_segment": None,
            "weakest_lift_segment": None,
            "significant_segments": [],
            "summary": "No runnable segment results were available.",
        }

    strongest = max(
        runnable_segments,
        key=lambda segment: segment["absolute_lift"],
    )

    weakest = min(
        runnable_segments,
        key=lambda segment: segment["absolute_lift"],
    )

    significant_segments = [
        segment for segment in runnable_segments
        if segment.get("statistically_significant")
    ]

    return {
        "segments_evaluated": len(runnable_segments),
        "strongest_lift_segment": strongest,
        "weakest_lift_segment": weakest,
        "significant_segments": significant_segments,
        "summary": (
            f"{len(runnable_segments)} segments evaluated. "
            f"Strongest lift: {strongest['segment_label']} "
            f"({strongest['absolute_lift_percentage_points']:.2f} pp). "
            f"Weakest lift: {weakest['segment_label']} "
            f"({weakest['absolute_lift_percentage_points']:.2f} pp)."
        ),
    }
