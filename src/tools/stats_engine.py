"""
ClaimCheck Statistical Evidence Engine

This module performs deterministic statistical validation.

Purpose:
- run treatment/control statistical tests
- calculate lift, p-values, and confidence intervals
- check treatment/control balance on covariates
- avoid using LLMs for statistical calculation
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint


def get_two_groups(
    df: pd.DataFrame,
    treatment_col: str,
) -> Tuple[Any, Any]:
    """
    Return the two observed treatment values.

    Raises an error if the treatment column does not contain exactly two groups.
    """
    groups = sorted(df[treatment_col].dropna().unique().tolist())

    if len(groups) != 2:
        raise ValueError(
            f"Expected exactly two treatment groups in '{treatment_col}', found {len(groups)}."
        )

    return groups[0], groups[1]


def check_group_balance(
    df: pd.DataFrame,
    treatment_col: str,
    covariates: Optional[List[str]] = None,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Check whether treatment/control groups are balanced on observable covariates.

    Numeric covariates use a two-sample t-test.
    Binary/categorical covariates use a chi-square test.
    """
    covariates = covariates or []

    if not covariates:
        return {
            "balance_checked": False,
            "balanced": None,
            "reason": "No covariates provided for balance check.",
            "covariate_results": [],
        }

    control_value, treatment_value = get_two_groups(df, treatment_col)

    results = []

    for covariate in covariates:
        if covariate not in df.columns:
            results.append({
                "covariate": covariate,
                "test": "not_run",
                "p_value": None,
                "balanced": None,
                "reason": "Covariate not found in dataset.",
            })
            continue

        control_series = df.loc[df[treatment_col] == control_value, covariate].dropna()
        treatment_series = df.loc[df[treatment_col] == treatment_value, covariate].dropna()

        if pd.api.types.is_numeric_dtype(df[covariate]):
            stat, p_value = stats.ttest_ind(
                treatment_series,
                control_series,
                equal_var=False,
                nan_policy="omit",
            )

            test_name = "two_sample_t_test"

        else:
            contingency = pd.crosstab(df[treatment_col], df[covariate])
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

            test_name = "chi_square_test"

        results.append({
            "covariate": covariate,
            "test": test_name,
            "p_value": float(p_value),
            "balanced": bool(p_value >= alpha),
            "alpha": alpha,
        })

    valid_results = [
        item for item in results
        if item["balanced"] is not None
    ]

    overall_balanced = (
        all(item["balanced"] for item in valid_results)
        if valid_results
        else None
    )

    return {
        "balance_checked": True,
        "balanced": overall_balanced,
        "alpha": alpha,
        "covariate_results": results,
    }


def run_two_proportion_test(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Run a two-proportion z-test for a binary outcome and binary treatment.

    Returns treatment/control rates, lift, p-value, and confidence interval.
    """
    control_value, treatment_value = get_two_groups(df, treatment_col)

    control = df[df[treatment_col] == control_value]
    treatment = df[df[treatment_col] == treatment_value]

    control_n = int(control[outcome_col].notna().sum())
    treatment_n = int(treatment[outcome_col].notna().sum())

    control_successes = int(control[outcome_col].sum())
    treatment_successes = int(treatment[outcome_col].sum())

    control_rate = control_successes / control_n
    treatment_rate = treatment_successes / treatment_n

    lift = treatment_rate - control_rate

    count = np.array([treatment_successes, control_successes])
    nobs = np.array([treatment_n, control_n])

    z_stat, p_value = proportions_ztest(count=count, nobs=nobs)

    ci_treatment_low, ci_treatment_high = proportion_confint(
        count=treatment_successes,
        nobs=treatment_n,
        alpha=alpha,
        method="normal",
    )

    ci_control_low, ci_control_high = proportion_confint(
        count=control_successes,
        nobs=control_n,
        alpha=alpha,
        method="normal",
    )

    lift_ci_low = ci_treatment_low - ci_control_high
    lift_ci_high = ci_treatment_high - ci_control_low

    return {
        "method": "two_proportion_test",
        "control_value": control_value,
        "treatment_value": treatment_value,
        "control_n": control_n,
        "treatment_n": treatment_n,
        "control_successes": control_successes,
        "treatment_successes": treatment_successes,
        "control_rate": float(control_rate),
        "treatment_rate": float(treatment_rate),
        "absolute_lift": float(lift),
        "absolute_lift_percentage_points": float(lift * 100),
        "relative_lift": float(lift / control_rate) if control_rate != 0 else None,
        "z_stat": float(z_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "statistically_significant": bool(p_value < alpha),
        "lift_confidence_interval": {
            "low": float(lift_ci_low),
            "high": float(lift_ci_high),
            "low_percentage_points": float(lift_ci_low * 100),
            "high_percentage_points": float(lift_ci_high * 100),
        },
    }


def run_two_sample_t_test(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Run a Welch two-sample t-test for a numeric outcome and binary treatment.
    """
    control_value, treatment_value = get_two_groups(df, treatment_col)

    control = df.loc[df[treatment_col] == control_value, outcome_col].dropna()
    treatment = df.loc[df[treatment_col] == treatment_value, outcome_col].dropna()

    t_stat, p_value = stats.ttest_ind(
        treatment,
        control,
        equal_var=False,
        nan_policy="omit",
    )

    control_mean = float(control.mean())
    treatment_mean = float(treatment.mean())
    difference = treatment_mean - control_mean

    return {
        "method": "two_sample_t_test",
        "control_value": control_value,
        "treatment_value": treatment_value,
        "control_n": int(control.shape[0]),
        "treatment_n": int(treatment.shape[0]),
        "control_mean": control_mean,
        "treatment_mean": treatment_mean,
        "absolute_difference": float(difference),
        "relative_difference": float(difference / control_mean) if control_mean != 0 else None,
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "statistically_significant": bool(p_value < alpha),
    }


def run_statistical_validation(
    df: pd.DataFrame,
    method_selection: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run statistical validation based on selected method.
    """
    selected_method = method_selection.get("selected_method")

    outcome_col = config.get("outcome_col")
    treatment_col = config.get("treatment_col")
    covariates = config.get("covariates", [])
    alpha = config.get("alpha", 0.05)

    if selected_method == "two_proportion_test":
        statistical_result = run_two_proportion_test(
            df=df,
            outcome_col=outcome_col,
            treatment_col=treatment_col,
            alpha=alpha,
        )

    elif selected_method == "two_sample_t_test":
        statistical_result = run_two_sample_t_test(
            df=df,
            outcome_col=outcome_col,
            treatment_col=treatment_col,
            alpha=alpha,
        )

    elif selected_method == "descriptive_only":
        statistical_result = {
            "method": "descriptive_only",
            "statistical_test_run": False,
            "reason": "Descriptive claim selected. No causal or comparative statistical test required.",
        }

    else:
        return {
            "validation_runnable": False,
            "human_review_required": True,
            "reason": f"Selected method '{selected_method}' is not currently runnable.",
            "statistical_result": None,
            "balance_result": None,
        }

    balance_result = None

    if treatment_col and treatment_col in df.columns:
        balance_result = check_group_balance(
            df=df,
            treatment_col=treatment_col,
            covariates=covariates,
            alpha=alpha,
        )

    return {
        "validation_runnable": True,
        "human_review_required": False,
        "selected_method": selected_method,
        "statistical_result": statistical_result,
        "balance_result": balance_result,
    }
