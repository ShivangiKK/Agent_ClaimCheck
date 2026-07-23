import pandas as pd

from src.tools.data_profiler import profile_dataset
from src.tools.method_selector import infer_claim_intent, select_method


def test_infer_claim_intent_detects_prescriptive_and_causal():
    claim = "The campaign drove purchases and should be rolled out broadly."

    result = infer_claim_intent(claim)

    assert "prescriptive_recommendation" in result["detected_intents"]
    assert "causal_impact" in result["detected_intents"]


def test_select_method_two_proportion_test():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "test": [0, 0, 1, 1],
        "purchase": [0, 1, 0, 1],
        "income": [50, 60, 70, 80],
    })

    config = {
        "outcome_col": "purchase",
        "treatment_col": "test",
        "unit_id_col": "id",
    }

    profile = profile_dataset(df, config)
    result = select_method(
        claim="The campaign drove purchases and should be reviewed for rollout.",
        profile=profile,
        config=config,
    )

    assert result["selected_method"] == "two_proportion_test"
    assert result["auto_runnable"] is True
    assert result["human_review_required"] is False


def test_select_method_routes_predictive_claim_to_review():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "churn": [0, 1, 0, 1],
        "usage": [20, 5, 30, 8],
        "income": [50, 60, 70, 80],
    })

    config = {
        "outcome_col": "churn",
        "treatment_col": None,
        "unit_id_col": "id",
    }

    profile = profile_dataset(df, config)
    result = select_method(
        claim="This score predicts which customers are likely to churn.",
        profile=profile,
        config=config,
    )

    assert result["selected_method"] == "predictive_driver_review"
    assert result["human_review_required"] is True


def test_select_method_routes_unknown_to_human_review():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "metric": [10, 20, 30],
    })

    config = {
        "outcome_col": "metric",
        "treatment_col": None,
    }

    profile = profile_dataset(df, config)
    result = select_method(
        claim="Please evaluate this business situation.",
        profile=profile,
        config=config,
    )

    assert result["selected_method"] == "human_review"
    assert result["human_review_required"] is True
