"""
ClaimCheck Streamlit App

Run with:
streamlit run app.py

This app supports two modes:
1. Deterministic workflow mode
2. CrewAI agent workflow mode

CrewAI mode requires:
- crew.py with run_claimcheck_agentic_workflow()
- .env file with GEMINI_API_KEY
"""

from typing import Any, Dict, List
import json

import pandas as pd
import streamlit as st

from src.tools.security_gate import run_security_gate, summarize_security_result
from src.tools.data_profiler import profile_dataset, summarize_dataset_profile
from src.tools.method_selector import select_method
from src.tools.stats_engine import run_statistical_validation
from src.tools.business_impact import (
    calculate_business_impact,
    calculate_segment_business_impact,
    identify_financially_positive_segments,
    identify_strongest_business_segment,
    summarize_business_impact,
)
from src.tools.segment_analysis import (
    run_segment_effects,
    run_intersectional_segment_effects,
    summarize_segment_results,
)
from src.tools.language_guardrail import (
    scan_for_blocked_language,
    rewrite_claim_language,
)


st.set_page_config(
    page_title="ClaimCheck",
    page_icon="✅",
    layout="wide",
)


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Load CSV or Excel file into a dataframe."""
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if uploaded_file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")


def format_pct(value: float) -> str:
    """Format decimal as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def format_pp(value: float) -> str:
    """Format percentage-point value."""
    if value is None:
        return "N/A"
    return f"{value:.2f} pp"


def build_executive_verdict(
    claim: str,
    method_selection: Dict[str, Any],
    validation_result: Dict[str, Any],
    business_impact: Dict[str, Any],
    language_scan: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a deterministic executive verdict for the Streamlit prototype.
    CrewAI mode separately produces an LLM-generated governed brief.
    """
    statistical_result = validation_result.get("statistical_result") or {}

    statistically_significant = statistical_result.get("statistically_significant")
    financially_positive = business_impact.get("financially_positive")
    language_safe = language_scan.get("language_safe")

    review_reasons: List[str] = []

    if not validation_result.get("validation_runnable"):
        review_reasons.append("Statistical validation is not runnable for the selected method.")

    if statistically_significant is False:
        review_reasons.append("The statistical result is not significant.")

    if financially_positive is False:
        review_reasons.append("The business impact is negative under the provided assumptions.")

    if language_safe is False:
        review_reasons.append("The submitted claim contains language that exceeds the selected evidence tier.")

    if method_selection.get("human_review_required"):
        review_reasons.append("The selected method requires human review.")

    if review_reasons:
        decision = "Human review required before this claim enters an executive deck."
    else:
        decision = "Claim appears supported under the current prototype checks."

    return {
        "decision": decision,
        "review_reasons": review_reasons,
        "claim": claim,
    }


def run_deterministic_claimcheck(
    df: pd.DataFrame,
    claim: str,
    config: Dict[str, Any],
    evidence_tier: str,
) -> Dict[str, Any]:
    """
    Run the deterministic ClaimCheck workflow directly.

    This is the non-LLM baseline used for reliability, debugging, and comparison.
    """
    security_result = run_security_gate(
        claim=claim,
        column_names=df.columns.tolist(),
        sample_rows=df.head(5).to_dict(orient="records"),
    )

    if not security_result["security_passed"]:
        return {
            "mode": "deterministic",
            "stopped": True,
            "stop_reason": "Security gate failed.",
            "security_result": security_result,
        }

    profile = profile_dataset(df, config)

    method_selection = select_method(
        claim=claim,
        profile=profile,
        config=config,
    )

    validation_result = run_statistical_validation(
        df=df,
        method_selection=method_selection,
        config=config,
    )

    business_impact = {
        "business_impact_runnable": False,
        "reason": "Business impact not run because statistical validation was not runnable.",
    }

    segment_summary = {
        "segments_evaluated": 0,
        "summary": "No segment review was run.",
    }

    enriched_segments = []

    if validation_result.get("validation_runnable"):
        statistical_result = validation_result.get("statistical_result") or {}

        business_impact = calculate_business_impact(
            statistical_result=statistical_result,
            business_value_per_success=config["business_value_per_success"],
            intervention_cost_per_success=config["intervention_cost_per_success"],
        )

        segment_cols = config.get("segment_cols", [])

        if segment_cols and statistical_result.get("method") == "two_proportion_test":
            segment_results = run_segment_effects(
                df=df,
                outcome_col=config["outcome_col"],
                treatment_col=config["treatment_col"],
                segment_cols=segment_cols,
                alpha=config.get("alpha", 0.05),
                min_segment_size=config.get("min_segment_size", 30),
            )

            intersectional_results = run_intersectional_segment_effects(
                df=df,
                outcome_col=config["outcome_col"],
                treatment_col=config["treatment_col"],
                segment_cols=segment_cols,
                alpha=config.get("alpha", 0.05),
                min_segment_size=config.get("min_segment_size", 30),
            )

            combined_segments = segment_results + intersectional_results
            segment_summary = summarize_segment_results(combined_segments)

            enriched_segments = calculate_segment_business_impact(
                segment_results=[
                    segment for segment in combined_segments
                    if segment.get("segment_runnable")
                ],
                business_value_per_success=config["business_value_per_success"],
                intervention_cost_per_success=config["intervention_cost_per_success"],
            )

    language_scan = scan_for_blocked_language(
        text=claim,
        evidence_tier=evidence_tier,
    )

    rewritten_result = None

    if not language_scan.get("language_safe"):
        rewritten_result = rewrite_claim_language(
            text=claim,
            evidence_tier=evidence_tier,
        )

    verdict = build_executive_verdict(
        claim=claim,
        method_selection=method_selection,
        validation_result=validation_result,
        business_impact=business_impact,
        language_scan=language_scan,
    )

    return {
        "mode": "deterministic",
        "stopped": False,
        "claim": claim,
        "config": config,
        "security_result": security_result,
        "dataset_profile": profile,
        "method_selection": method_selection,
        "validation_result": validation_result,
        "business_impact": business_impact,
        "segment_summary": segment_summary,
        "enriched_segments": enriched_segments,
        "language_scan": language_scan,
        "rewritten_result": rewritten_result,
        "verdict": verdict,
    }


def try_run_crewai_workflow(
    df: pd.DataFrame,
    claim: str,
    config: Dict[str, Any],
    evidence_tier: str,
) -> Dict[str, Any]:
    """
    Run the CrewAI-backed workflow.

    This expects crew.py to define:
    run_claimcheck_agentic_workflow(df, claim, config, evidence_tier)
    """
    try:
        from crew import run_claimcheck_agentic_workflow
    except Exception as error:
        return {
            "mode": "crewai",
            "stopped": True,
            "error": (
                "CrewAI workflow is not available. Check that crew.py contains "
                "run_claimcheck_agentic_workflow()."
            ),
            "details": str(error),
        }

    try:
        return run_claimcheck_agentic_workflow(
            df=df,
            claim=claim,
            config=config,
            evidence_tier=evidence_tier,
        )
    except Exception as error:
        return {
            "mode": "crewai",
            "stopped": True,
            "error": "CrewAI workflow failed.",
            "details": str(error),
        }


st.title("ClaimCheck")
st.subheader("Evidence-Governed Business Claim Review Agent")

st.write(
    "ClaimCheck reviews whether a business claim is statistically supported, "
    "commercially justified, and safe to communicate before it enters an executive report or slide deck."
)

with st.expander("Architecture", expanded=False):
    st.code(
        "Streamlit → CrewAI Agents → CrewAI Tool Wrappers → Deterministic Evidence Engine → Governed Executive Brief",
        language="text",
    )

    st.markdown(
        """
| Layer | Role |
|---|---|
| Streamlit | User interface |
| CrewAI | Agent orchestration |
| Gemini | LLM reasoning and executive communication |
| CrewAI tools | Bridge between agents and deterministic tools |
| `src/tools/` | Deterministic evidence engine |
"""
    )

workflow_mode = st.radio(
    "Workflow mode",
    options=[
        "Deterministic workflow",
        "CrewAI agent workflow",
    ],
    horizontal=True,
)

if workflow_mode == "CrewAI agent workflow":
    st.info(
        "CrewAI mode uses Gemini, CrewAI agents, and ClaimCheck tool wrappers. "
        "It requires a local `.env` file with `GEMINI_API_KEY`."
    )
else:
    st.info(
        "Deterministic mode runs the validation tools directly. "
        "This is the reliability baseline."
    )

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel dataset",
    type=["csv", "xlsx", "xls"],
)

claim = st.text_area(
    "Business claim to review",
    value="The campaign drove purchases and should be rolled out broadly.",
)

if uploaded_file is not None:
    df = load_uploaded_file(uploaded_file)

    st.success("Dataset loaded successfully.")

    with st.expander("Preview dataset", expanded=True):
        st.dataframe(df.head(20), use_container_width=True)

    columns = df.columns.tolist()

    st.markdown("## Configure analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        outcome_col = st.selectbox("Outcome column", options=columns)

    with col2:
        treatment_col = st.selectbox("Treatment/control column", options=columns)

    with col3:
        unit_id_col = st.selectbox("Unit ID column", options=[None] + columns)

    covariates = st.multiselect(
        "Covariates for balance check",
        options=columns,
        default=[],
    )

    segment_cols = st.multiselect(
        "Segment columns",
        options=columns,
        default=[],
    )

    col4, col5 = st.columns(2)

    with col4:
        business_value_per_success = st.number_input(
            "Business value per success",
            min_value=0.0,
            value=37.5,
            step=1.0,
        )

    with col5:
        intervention_cost_per_success = st.number_input(
            "Intervention cost per success",
            min_value=0.0,
            value=25.0,
            step=1.0,
        )

    alpha = st.number_input(
        "Significance level",
        min_value=0.001,
        max_value=0.20,
        value=0.05,
        step=0.01,
    )

    evidence_tier = st.selectbox(
        "Evidence tier for language guardrail",
        options=["Descriptive", "Predictive", "Suggestive", "Causal", "Decision-Ready"],
        index=3,
    )

    config = {
        "dataset_name": uploaded_file.name,
        "outcome_col": outcome_col,
        "treatment_col": treatment_col,
        "unit_id_col": unit_id_col,
        "covariates": covariates,
        "segment_cols": segment_cols,
        "business_value_per_success": business_value_per_success,
        "intervention_cost_per_success": intervention_cost_per_success,
        "alpha": alpha,
        "min_segment_size": 30,
    }

    if st.button("Run ClaimCheck", type="primary"):
        with st.spinner("Running ClaimCheck workflow..."):
            if workflow_mode == "CrewAI agent workflow":
                result = try_run_crewai_workflow(
                    df=df,
                    claim=claim,
                    config=config,
                    evidence_tier=evidence_tier,
                )
            else:
                result = run_deterministic_claimcheck(
                    df=df,
                    claim=claim,
                    config=config,
                    evidence_tier=evidence_tier,
                )

        st.markdown("## ClaimCheck Result")

        if result.get("stopped"):
            st.error(result.get("error") or result.get("stop_reason") or "Workflow stopped.")

            if result.get("details"):
                st.caption(result["details"])

            with st.expander("Debug details", expanded=False):
                st.json(result)

            st.stop()

        if result.get("mode") == "crewai":
            st.success("CrewAI agent workflow completed.")

            st.markdown("### Agent-generated executive brief")
            st.write(result.get("executive_brief", "No executive brief returned."))

            evidence_packet = result.get("evidence_packet", {})

            if evidence_packet:
                st.markdown("### Deterministic evidence used by agents")

                col_a, col_b, col_c = st.columns(3)

                statistical_result = (
                    evidence_packet
                    .get("validation_result", {})
                    .get("statistical_result", {})
                )

                business_impact = evidence_packet.get("business_impact", {})

                col_a.metric(
                    "Selected method",
                    evidence_packet.get("method_selection", {}).get("selected_method", "N/A"),
                )

                col_b.metric(
                    "Human review",
                    "Yes" if evidence_packet.get("human_review_required") else "No",
                )

                col_c.metric(
                    "Business positive",
                    "Yes" if business_impact.get("financially_positive") else "No",
                )

                if statistical_result.get("method") == "two_proportion_test":
                    metric_cols = st.columns(4)

                    metric_cols[0].metric(
                        "Control rate",
                        format_pct(statistical_result["control_rate"]),
                    )
                    metric_cols[1].metric(
                        "Treatment rate",
                        format_pct(statistical_result["treatment_rate"]),
                    )
                    metric_cols[2].metric(
                        "Lift",
                        format_pp(statistical_result["absolute_lift_percentage_points"]),
                    )
                    metric_cols[3].metric(
                        "p-value",
                        f"{statistical_result['p_value']:.4g}",
                    )

                review_reasons = evidence_packet.get("review_reasons", [])
                if review_reasons:
                    st.markdown("### Human-review reasons")
                    for reason in review_reasons:
                        st.write(f"- {reason}")

            with st.expander("Full CrewAI result", expanded=False):
                st.json(result)

            st.download_button(
                label="Download CrewAI result JSON",
                data=json.dumps(result, indent=2, default=str),
                file_name="claimcheck_crewai_result.json",
                mime="application/json",
            )

        else:
            st.success("Deterministic workflow completed.")

            st.markdown("### 1. Lovelace Security Check")
            if result["security_result"]["security_passed"]:
                st.success(summarize_security_result(result["security_result"]))
            else:
                st.error(summarize_security_result(result["security_result"]))

            st.markdown("### 2. Dataset Profile")
            st.info(summarize_dataset_profile(result["dataset_profile"]))

            with st.expander("Full dataset profile", expanded=False):
                st.json(result["dataset_profile"])

            st.markdown("### 3. Fisher Method Selection")
            st.write(result["method_selection"]["reason"])

            with st.expander("Method selection details", expanded=False):
                st.json(result["method_selection"])

            st.markdown("### 4. Statistical Validation")

            statistical_result = result["validation_result"].get("statistical_result") or {}

            if statistical_result.get("method") == "two_proportion_test":
                metric_cols = st.columns(4)

                metric_cols[0].metric(
                    "Control rate",
                    format_pct(statistical_result["control_rate"]),
                )
                metric_cols[1].metric(
                    "Treatment rate",
                    format_pct(statistical_result["treatment_rate"]),
                )
                metric_cols[2].metric(
                    "Lift",
                    format_pp(statistical_result["absolute_lift_percentage_points"]),
                )
                metric_cols[3].metric(
                    "p-value",
                    f"{statistical_result['p_value']:.4g}",
                )

            with st.expander("Statistical validation details", expanded=False):
                st.json(result["validation_result"])

            st.markdown("### 5. Business Impact")

            business_impact = result["business_impact"]

            if business_impact.get("business_impact_runnable"):
                if business_impact["financially_positive"]:
                    st.success(summarize_business_impact(business_impact))
                else:
                    st.warning(summarize_business_impact(business_impact))
            else:
                st.info(business_impact.get("reason"))

            with st.expander("Business impact details", expanded=False):
                st.json(business_impact)

            st.markdown("### 6. Segment Review")

            st.write(result["segment_summary"]["summary"])

            enriched_segments = result.get("enriched_segments", [])

            if enriched_segments:
                st.dataframe(pd.DataFrame(enriched_segments), use_container_width=True)

                positive_segments = identify_financially_positive_segments(enriched_segments)
                strongest_business_segment = identify_strongest_business_segment(enriched_segments)

                if positive_segments:
                    st.success(f"{len(positive_segments)} financially positive segment(s) identified.")
                else:
                    st.warning("No financially positive segment identified under the current assumptions.")

                if strongest_business_segment:
                    st.info(
                        "Strongest business segment: "
                        f"{strongest_business_segment.get('segment_label')} "
                        f"with incremental expected value per unit of "
                        f"${strongest_business_segment.get('incremental_expected_value_per_unit'):.4f}."
                    )

            st.markdown("### 7. Language Guardrail")

            language_scan = result["language_scan"]

            if language_scan.get("language_safe"):
                st.success("Claim language is allowed under the selected evidence tier.")
            else:
                st.warning("Claim language exceeds the selected evidence tier.")

                rewritten_result = result.get("rewritten_result")
                if rewritten_result:
                    st.write("Suggested safer wording:")
                    st.info(rewritten_result["rewritten_text"])

            with st.expander("Language guardrail details", expanded=False):
                st.json(language_scan)

            st.markdown("### 8. Executive Verdict")

            verdict = result["verdict"]

            if verdict["review_reasons"]:
                st.error(verdict["decision"])
                for reason in verdict["review_reasons"]:
                    st.write(f"- {reason}")
            else:
                st.success(verdict["decision"])

            st.download_button(
                label="Download evidence packet JSON",
                data=json.dumps(result, indent=2, default=str),
                file_name="claimcheck_evidence_packet.json",
                mime="application/json",
            )

else:
    st.info("Upload a CSV or Excel file to begin.")
