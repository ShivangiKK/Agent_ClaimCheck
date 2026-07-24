"""
ClaimCheck CrewAI Workflow

This file runs the actual agentic layer for ClaimCheck.

Architecture:
Streamlit / Python caller
    ↓
CrewAI agents
    ↓
ClaimCheck CrewAI tool wrappers
    ↓
Deterministic src/tools evidence engine
    ↓
LLM-generated governed executive brief

Required local .env file:
GEMINI_API_KEY=your_real_key_here
MODEL=gemini/gemini-2.5-flash
"""

from typing import Any, Dict
import json
import os
import uuid

import pandas as pd
from dotenv import load_dotenv

from crewai import Agent, Crew, Process, Task, LLM

from src.crew_tools.claimcheck_tools import (
    register_dataframe,
    get_claimcheck_tools,
)

from src.tools.security_gate import run_security_gate
from src.tools.data_profiler import profile_dataset
from src.tools.method_selector import select_method
from src.tools.stats_engine import run_statistical_validation
from src.tools.business_impact import calculate_business_impact
from src.tools.segment_analysis import (
    run_segment_effects,
    run_intersectional_segment_effects,
    summarize_segment_results,
)
from src.tools.language_guardrail import (
    scan_for_blocked_language,
    rewrite_claim_language,
)


load_dotenv()


def _resolve_model_name() -> str:
    """
    CrewAI uses LiteLLM model naming.
    Gemini models are safest when written as gemini/<model-name>.
    """
    model = os.getenv("MODEL", "gemini/gemini-2.5-flash")

    if model.startswith("gemini/"):
        return model

    return f"gemini/{model}"


def _get_llm() -> LLM:
    """
    Create the Gemini LLM object for CrewAI.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing GEMINI_API_KEY. Create a local .env file with your Gemini API key."
        )

    return LLM(
        model=_resolve_model_name(),
        api_key=api_key,
        temperature=0.2,
    )


def _json_dumps(data: Dict[str, Any]) -> str:
    """
    JSON dump helper that handles numpy/pandas values.
    """
    return json.dumps(data, indent=2, default=str)


def build_deterministic_evidence_packet(
    df: pd.DataFrame,
    claim: str,
    config: Dict[str, Any],
    evidence_tier: str,
) -> Dict[str, Any]:
    """
    Build the deterministic evidence packet before the LLM writes anything.

    This is intentional:
    - deterministic tools calculate evidence;
    - CrewAI agents interpret and communicate;
    - the LLM cannot invent statistics or business impact.
    """
    security_result = run_security_gate(
        claim=claim,
        column_names=df.columns.tolist(),
        sample_rows=df.head(5).to_dict(orient="records"),
    )

    if not security_result["security_passed"]:
        return {
            "claim": claim,
            "config": config,
            "evidence_tier": evidence_tier,
            "stopped": True,
            "stop_reason": "Security gate failed.",
            "security_result": security_result,
        }

    dataset_profile = profile_dataset(df, config)

    method_selection = select_method(
        claim=claim,
        profile=dataset_profile,
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

    segment_results = []
    segment_summary = {
        "segments_evaluated": 0,
        "summary": "No segment analysis was run.",
    }

    if validation_result.get("validation_runnable"):
        statistical_result = validation_result.get("statistical_result") or {}

        business_impact = calculate_business_impact(
            statistical_result=statistical_result,
            business_value_per_success=config.get("business_value_per_success", 0.0),
            intervention_cost_per_success=config.get("intervention_cost_per_success", 0.0),
        )

        if (
            statistical_result.get("method") == "two_proportion_test"
            and config.get("segment_cols")
        ):
            base_segment_results = run_segment_effects(
                df=df,
                outcome_col=config["outcome_col"],
                treatment_col=config["treatment_col"],
                segment_cols=config.get("segment_cols", []),
                alpha=config.get("alpha", 0.05),
                min_segment_size=config.get("min_segment_size", 30),
            )

            intersectional_segment_results = run_intersectional_segment_effects(
                df=df,
                outcome_col=config["outcome_col"],
                treatment_col=config["treatment_col"],
                segment_cols=config.get("segment_cols", []),
                alpha=config.get("alpha", 0.05),
                min_segment_size=config.get("min_segment_size", 30),
            )

            segment_results = base_segment_results + intersectional_segment_results
            segment_summary = summarize_segment_results(segment_results)

    language_scan = scan_for_blocked_language(
        text=claim,
        evidence_tier=evidence_tier,
    )

    rewritten_language = None

    if not language_scan.get("language_safe"):
        rewritten_language = rewrite_claim_language(
            text=claim,
            evidence_tier=evidence_tier,
        )

    review_reasons = []

    if method_selection.get("human_review_required"):
        review_reasons.append("Selected method requires human review.")

    if not validation_result.get("validation_runnable"):
        review_reasons.append("Statistical validation is not runnable.")

    statistical_result = validation_result.get("statistical_result") or {}

    if statistical_result.get("statistically_significant") is False:
        review_reasons.append("Statistical result is not significant.")

    if business_impact.get("financially_positive") is False:
        review_reasons.append("Business impact is negative under the provided assumptions.")

    if language_scan.get("language_safe") is False:
        review_reasons.append("Original claim language exceeds the selected evidence tier.")

    if segment_summary.get("segments_evaluated", 0) > 0 and business_impact.get("financially_positive") is False:
        review_reasons.append(
            "Segment-level opportunities may exist, but broad rollout is not financially supported."
        )

    return {
        "claim": claim,
        "config": config,
        "evidence_tier": evidence_tier,
        "stopped": False,
        "security_result": security_result,
        "dataset_profile": dataset_profile,
        "method_selection": method_selection,
        "validation_result": validation_result,
        "business_impact": business_impact,
        "segment_results": segment_results,
        "segment_summary": segment_summary,
        "language_scan": language_scan,
        "rewritten_language": rewritten_language,
        "human_review_required": len(review_reasons) > 0,
        "review_reasons": review_reasons,
    }


def build_claimcheck_agents(llm: LLM, tools: list) -> Dict[str, Agent]:
    """
    Build ClaimCheck CrewAI agents.
    """
    lovelace = Agent(
        role="AI Safety and Workflow Control Lead",
        goal=(
            "Ensure business claims and dataset metadata are safe before analysis. "
            "Prevent prompt injection and unsafe LLM exposure."
        ),
        backstory=(
            "You are Lovelace, the control layer for ClaimCheck. "
            "You protect the workflow before analytical agents receive the request."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )

    toulmin = Agent(
        role="Senior Analyst, Claim Structuring",
        goal=(
            "Convert stakeholder language into a structured, testable analytical claim. "
            "Identify claim type, evidence strength, and missing context."
        ),
        backstory=(
            "You are Toulmin, responsible for transforming messy business language "
            "into structured analytical reasoning."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )

    fisher = Agent(
        role="Decision Scientist, Measurement Design",
        goal=(
            "Select the appropriate method family and explain why that method is appropriate. "
            "Do not invent unsupported analytical pathways."
        ),
        backstory=(
            "You are Fisher, the measurement design expert. "
            "You use the method registry and deterministic tools to route the claim safely."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )

    wald = Agent(
        role="Senior Analyst, Risk and Measurement",
        goal=(
            "Review the evidence packet for overclaiming, weak evidence, negative economics, "
            "segment conflict, and human-review triggers."
        ),
        backstory=(
            "You are Wald, responsible for identifying what the evidence does not prove. "
            "You prevent statistically true findings from becoming unsupported business decisions."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )

    minto = Agent(
        role="Director, Analytics Communication",
        goal=(
            "Write an executive-facing brief using only validated evidence. "
            "Respect the evidence tier and language guardrails."
        ),
        backstory=(
            "You are Minto, responsible for concise executive communication. "
            "You translate validated evidence into decision-safe business language."
        ),
        llm=llm,
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )

    return {
        "lovelace": lovelace,
        "toulmin": toulmin,
        "fisher": fisher,
        "wald": wald,
        "minto": minto,
    }


def run_claimcheck_agentic_workflow(
    df: pd.DataFrame,
    claim: str,
    config: Dict[str, Any],
    evidence_tier: str = "Causal",
) -> Dict[str, Any]:
    """
    Run the ClaimCheck CrewAI-backed workflow.

    This function is what Streamlit will call.
    """
    dataset_id = f"dataset_{uuid.uuid4().hex[:8]}"
    register_dataframe(dataset_id, df)

    config = {
        **config,
        "dataset_id": dataset_id,
    }

    evidence_packet = build_deterministic_evidence_packet(
        df=df,
        claim=claim,
        config=config,
        evidence_tier=evidence_tier,
    )

    if evidence_packet.get("stopped"):
        return {
            "mode": "crewai",
            "stopped": True,
            "error": evidence_packet.get("stop_reason"),
            "evidence_packet": evidence_packet,
        }

    llm = _get_llm()
    tools = get_claimcheck_tools()
    agents = build_claimcheck_agents(llm=llm, tools=tools)

    evidence_packet_json = _json_dumps(evidence_packet)
    config_json = _json_dumps(config)

    safety_and_method_task = Task(
        description=f"""
You are reviewing a business claim using the ClaimCheck workflow.

Claim:
{claim}

Dataset ID:
{dataset_id}

Configuration JSON:
{config_json}

Evidence tier selected by user:
{evidence_tier}

Use the available ClaimCheck tools where useful:
- security_gate_tool
- data_profiler_tool
- method_selector_tool
- statistical_validation_tool
- business_impact_tool
- segment_analysis_tool
- language_guardrail_tool

Important constraints:
- Do not invent data, statistics, p-values, confidence intervals, or business impact.
- Deterministic tool outputs are the source of truth.
- If the evidence is insufficient for the requested claim strength, say so.
- Identify whether human review is required.

A deterministic evidence packet has already been generated below. Use it as the source of truth:

{evidence_packet_json}
""",
        expected_output="""
A concise analytical review with:
1. security status,
2. claim type and requested strength,
3. selected method,
4. statistical evidence,
5. business-impact evidence,
6. segment insight,
7. language-risk assessment,
8. human-review decision.
""",
        agent=agents["wald"],
    )

    executive_brief_task = Task(
        description=f"""
Write the final ClaimCheck executive brief.

Use only the evidence from the deterministic evidence packet and the prior agent review.

Claim:
{claim}

Evidence tier:
{evidence_tier}

Evidence packet:
{evidence_packet_json}

The brief must include:
1. Executive verdict
2. Evidence summary
3. Business impact
4. Segment insight, if available
5. Language safety assessment
6. Human-review reasons
7. Recommended next step

Rules:
- Do not invent numbers.
- Do not overstate causality.
- Do not say "approve rollout" unless the evidence is Decision-Ready and business impact is positive.
- If the claim says "drove" or "should roll out" but the business impact is negative, clearly block broad rollout language.
- Keep it concise and business-facing.
""",
        expected_output="""
A polished executive-facing ClaimCheck brief that is safe to place in a leadership review.
""",
        agent=agents["minto"],
        context=[safety_and_method_task],
    )

    crew = Crew(
        agents=[
            agents["wald"],
            agents["minto"],
        ],
        tasks=[
            safety_and_method_task,
            executive_brief_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    crew_output = crew.kickoff()

    executive_brief = getattr(crew_output, "raw", str(crew_output))

    return {
        "mode": "crewai",
        "stopped": False,
        "dataset_id": dataset_id,
        "claim": claim,
        "config": config,
        "evidence_tier": evidence_tier,
        "evidence_packet": evidence_packet,
        "executive_brief": executive_brief,
        "crew_output": str(crew_output),
    }


if __name__ == "__main__":
    print("ClaimCheck CrewAI workflow is ready.")
    print("Use run_claimcheck_agentic_workflow(df, claim, config, evidence_tier) from app.py.")
