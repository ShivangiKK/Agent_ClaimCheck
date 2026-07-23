from src.tools.business_impact import (
    calculate_business_impact,
    calculate_segment_business_impact,
    identify_financially_positive_segments,
    identify_strongest_business_segment,
    summarize_business_impact,
)


def test_calculate_business_impact_positive_case():
    statistical_result = {
        "method": "two_proportion_test",
        "control_rate": 0.05,
        "treatment_rate": 0.10,
        "treatment_n": 1000,
    }

    result = calculate_business_impact(
        statistical_result=statistical_result,
        business_value_per_success=100,
        intervention_cost_per_success=20,
    )

    assert result["business_impact_runnable"] is True
    assert result["financially_positive"] is True
    assert result["incremental_expected_value_per_unit"] > 0


def test_calculate_business_impact_negative_case():
    statistical_result = {
        "method": "two_proportion_test",
        "control_rate": 0.036,
        "treatment_rate": 0.077,
        "treatment_n": 28091,
    }

    result = calculate_business_impact(
        statistical_result=statistical_result,
        business_value_per_success=37.5,
        intervention_cost_per_success=25.0,
    )

    assert result["business_impact_runnable"] is True
    assert result["financially_positive"] is False
    assert result["incremental_expected_value_per_unit"] < 0


def test_business_impact_rejects_unsupported_method():
    statistical_result = {
        "method": "two_sample_t_test",
    }

    result = calculate_business_impact(
        statistical_result=statistical_result,
        business_value_per_success=100,
        intervention_cost_per_success=20,
    )

    assert result["business_impact_runnable"] is False


def test_calculate_segment_business_impact():
    segment_results = [
        {
            "segment_col": "gamer",
            "segment_value": 1,
            "control_rate": 0.05,
            "treatment_rate": 0.12,
            "treatment_n": 500,
            "absolute_lift": 0.07,
            "p_value": 0.001,
        },
        {
            "segment_col": "gamer",
            "segment_value": 0,
            "control_rate": 0.04,
            "treatment_rate": 0.03,
            "treatment_n": 500,
            "absolute_lift": -0.01,
            "p_value": 0.20,
        },
    ]

    result = calculate_segment_business_impact(
        segment_results=segment_results,
        business_value_per_success=100,
        intervention_cost_per_success=20,
    )

    assert len(result) == 2
    assert result[0]["business_impact_runnable"] is True
    assert "incremental_expected_value_per_unit" in result[0]


def test_identify_financially_positive_segments():
    enriched_segments = [
        {
            "segment_col": "gamer",
            "segment_value": 1,
            "business_impact_runnable": True,
            "financially_positive": True,
            "incremental_expected_value_per_unit": 2.0,
        },
        {
            "segment_col": "gamer",
            "segment_value": 0,
            "business_impact_runnable": True,
            "financially_positive": False,
            "incremental_expected_value_per_unit": -1.0,
        },
    ]

    positive_segments = identify_financially_positive_segments(enriched_segments)

    assert len(positive_segments) == 1
    assert positive_segments[0]["segment_value"] == 1


def test_identify_strongest_business_segment():
    enriched_segments = [
        {
            "segment_col": "gamer",
            "segment_value": 1,
            "business_impact_runnable": True,
            "incremental_expected_value_per_unit": 2.0,
        },
        {
            "segment_col": "gender",
            "segment_value": 0,
            "business_impact_runnable": True,
            "incremental_expected_value_per_unit": 3.0,
        },
    ]

    strongest = identify_strongest_business_segment(enriched_segments)

    assert strongest["segment_col"] == "gender"
    assert strongest["incremental_expected_value_per_unit"] == 3.0


def test_summarize_business_impact():
    business_impact = {
        "business_impact_runnable": True,
        "incremental_expected_value_per_unit": -0.3977,
        "total_incremental_expected_value": -11172.0,
        "financially_positive": False,
    }

    summary = summarize_business_impact(business_impact)

    assert "negative" in summary
    assert "Incremental expected value" in summary
