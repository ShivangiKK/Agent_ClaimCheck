import pandas as pd

from src.tools.segment_analysis import (
    run_segment_effects,
    run_intersectional_segment_effects,
    summarize_segment_results,
)


def test_run_segment_effects_returns_segment_results():
    df = pd.DataFrame({
        "test": [0, 0, 0, 1, 1, 1] * 20,
        "purchase": [0, 1, 0, 1, 1, 0] * 20,
        "gamer": [0, 0, 1, 0, 1, 1] * 20,
    })

    result = run_segment_effects(
        df=df,
        outcome_col="purchase",
        treatment_col="test",
        segment_cols=["gamer"],
        min_segment_size=10,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert "segment_col" in result[0]


def test_run_intersectional_segment_effects_returns_results():
    df = pd.DataFrame({
        "test": [0, 0, 0, 1, 1, 1] * 30,
        "purchase": [0, 1, 0, 1, 1, 0] * 30,
        "gender": [0, 1, 0, 1, 0, 1] * 30,
        "gamer": [0, 0, 1, 0, 1, 1] * 30,
    })

    result = run_intersectional_segment_effects(
        df=df,
        outcome_col="purchase",
        treatment_col="test",
        segment_cols=["gender", "gamer"],
        min_segment_size=10,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert "segment_label" in result[0]


def test_summarize_segment_results_identifies_strongest_segment():
    segment_results = [
        {
            "segment_label": "gamer=1",
            "segment_runnable": True,
            "absolute_lift": 0.08,
            "absolute_lift_percentage_points": 8.0,
            "statistically_significant": True,
        },
        {
            "segment_label": "gamer=0",
            "segment_runnable": True,
            "absolute_lift": -0.01,
            "absolute_lift_percentage_points": -1.0,
            "statistically_significant": False,
        },
    ]

    summary = summarize_segment_results(segment_results)

    assert summary["segments_evaluated"] == 2
    assert summary["strongest_lift_segment"]["segment_label"] == "gamer=1"
    assert summary["weakest_lift_segment"]["segment_label"] == "gamer=0"v
