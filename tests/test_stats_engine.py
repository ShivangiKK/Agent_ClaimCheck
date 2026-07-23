import pandas as pd

from src.tools.stats_engine import (
    check_group_balance,
    get_two_groups,
    run_statistical_validation,
    run_two_proportion_test,
    run_two_sample_t_test,
)


def test_get_two_groups_returns_two_values():
    df = pd.DataFrame({
        "test": [0, 0, 1, 1],
    })

    control, treatment = get_two_groups(df, "test")

    assert control == 0
    assert treatment == 1


def test_run_two_proportion_test_returns_lift_and_p_value():
    df = pd.DataFrame({
        "test": [0, 0, 0, 0, 1, 1, 1, 1],
        "purchase": [0, 0, 1, 0, 1, 1, 1, 0],
    })

    result = run_two_proportion_test(
        df=df,
        outcome_col="purchase",
        treatment_col="test",
    )

    assert result["method"] == "two_proportion_test"
    assert "absolute_lift" in result
    assert "p_value" in result
    assert result["control_n"] == 4
    assert result["treatment_n"] == 4


def test_run_two_sample_t_test_returns_difference_and_p_value():
    df = pd.DataFrame({
        "test": [0, 0, 0, 1, 1, 1],
        "revenue": [10, 12, 11, 15, 16, 14],
    })

    result = run_two_sample_t_test(
        df=df,
        outcome_col="revenue",
        treatment_col="test",
    )

    assert result["method"] == "two_sample_t_test"
    assert "absolute_difference" in result
    assert "p_value" in result
    assert result["control_n"] == 3
    assert result["treatment_n"] == 3


def test_check_group_balance_runs_on_covariates():
    df = pd.DataFrame({
        "test": [0, 0, 1, 1],
        "income": [50, 55, 52, 54],
    })

    result = check_group_balance(
        df=df,
        treatment_col="test",
        covariates=["income"],
    )

    assert result["balance_checked"] is True
    assert len(result["covariate_results"]) == 1
    assert result["covariate_results"][0]["covariate"] == "income"


def test_run_statistical_validation_uses_selected_method():
    df = pd.DataFrame({
        "test": [0, 0, 0, 0, 1, 1, 1, 1],
        "purchase": [0, 0, 1, 0, 1, 1, 1, 0],
        "income": [50, 55, 60, 58, 52, 57, 61, 59],
    })

    method_selection = {
        "selected_method": "two_proportion_test",
    }

    config = {
        "outcome_col": "purchase",
        "treatment_col": "test",
        "covariates": ["income"],
        "alpha": 0.05,
    }

    result = run_statistical_validation(
        df=df,
        method_selection=method_selection,
        config=config,
    )

    assert result["validation_runnable"] is True
    assert result["selected_method"] == "two_proportion_test"
    assert result["statistical_result"]["method"] == "two_proportion_test"
    assert result["balance_result"]["balance_checked"] is True
