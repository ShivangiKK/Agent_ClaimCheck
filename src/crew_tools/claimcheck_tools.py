
"""
ClaimCheck CrewAI Tool Wrappers

These tools expose ClaimCheck's deterministic Python modules to CrewAI agents.

Design principle:
- LLM agents reason, coordinate, and communicate.
- Deterministic tools calculate, validate, route, and enforce safety.
"""

from typing import Any, Dict, List, Type
import json

import pandas as pd
from pydantic import BaseModel, Field

from crewai.tools import BaseTool

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


DATAFRAME_REGISTRY: Dict[str, pd.DataFrame] = {}


def register_dataframe(dataset_id: str, df: pd.DataFrame) -> None:
    """
    Register a dataframe so CrewAI tools can reference it by dataset_id.

    This avoids passing the full dataset through LLM prompts.
    """
    DATAFRAME_REGISTRY[dataset_id] = df


def get_registered_dataframe(dataset_id: str) -> pd.DataFrame:
    """
    Retrieve a registered dataframe by dataset_id.
    """
    if dataset_id not in DATAFRAME_REGISTRY:
        raise ValueError(f"Dataset ID not found: {dataset_id}")

    return DATAFRAME_REGISTRY[dataset_id]


class SecurityGateInput(BaseModel):
    claim: str = Field(..., description="Business claim submitted by the user.")
    dataset_id: str = Field(..., description="Registered dataset identifier.")


class DataProfilerInput(BaseModel):
    dataset_id: str = Field(..., description="Registered dataset identifier.")
    config_json: str = Field(..., description="JSON string containing analysis configuration.")


class MethodSelectorInput(BaseModel):
    claim: str = Field(..., description="Business claim submitted by the user.")
    dataset_id: str = Field(..., description="Registered dataset identifier.")
    config_json: str = Field(..., description="JSON string containing analysis configuration.")


class StatisticalValidationInput(BaseModel):
    dataset_id: str = Field(..., description="Registered dataset identifier.")
    method_selection_json: str = Field(..., description="JSON string containing method selection output.")
    config_json: str = Field(..., description="JSON string containing analysis configuration.")


class BusinessImpactInput(BaseModel):
    statistical_result_json: str = Field(..., description="JSON string containing statistical result.")
    business_value_per_success: float = Field(..., description="Value of one successful outcome.")
    intervention_cost_per_success: float = Field(0.0, description="Cost associated with intervention or success.")


class SegmentAnalysisInput(BaseModel):
    dataset_id: str = Field(..., description="Registered dataset identifier.")
    config_json: str = Field(..., description="JSON string containing outcome, treatment, segment columns, and assumptions.")


class LanguageGuardrailInput(BaseModel):
    text: str = Field(..., description="Text to scan or rewrite.")
    evidence_tier: str = Field(..., description="Evidence tier: Descriptive, Predictive, Suggestive, Causal, or Decision-Ready.")


class SecurityGateTool(BaseTool):
    name: str = "security_gate_tool"
    description: str = (
        "Screens a business claim, dataset columns, and sample rows for prompt injection "
        "or unsafe instructions before any LLM processing."
    )
    args_schema: Type[BaseModel] = SecurityGateInput

    def _run(self, claim: str, dataset_id: str) -> str:
        df = get_registered_dataframe(dataset_id)

        result = run_security_gate(
            claim=claim,
            column_names=df.columns.tolist(),
            sample_rows=df.head(5).to_dict(orient="records"),
        )

        return json.dumps(result, indent=2)


class DataProfilerTool(BaseTool):
    name: str = "data_profiler_tool"
    description: str = (
        "Profiles a dataset, including row count, columns, data types, missing values, "
        "binary columns, possible ID columns, possible time columns, and config validation."
    )
    args_schema: Type[BaseModel] = DataProfilerInput

    def _run(self, dataset_id: str, config_json: str) -> str:
        df = get_registered_dataframe(dataset_id)
        config = json.loads(config_json)

        result = profile_dataset(df, config)

        return json.dumps(result, indent=2)


class MethodSelectorTool(BaseTool):
    name: str = "method_selector_tool"
    description: str = (
        "Selects the safest analytical method family based on the claim, dataset profile, "
        "and analysis configuration."
    )
    args_schema: Type[BaseModel] = MethodSelectorInput

    def _run(self, claim: str, dataset_id: str, config_json: str) -> str:
        df = get_registered_dataframe(dataset_id)
        config = json.loads(config_json)

        profile = profile_dataset(df, config)
        result = select_method(
            claim=claim,
            profile=profile,
            config=config,
        )

        return json.dumps(result, indent=2)


class StatisticalValidationTool(BaseTool):
    name: str = "statistical_validation_tool"
    description: str = (
        "Runs deterministic statistical validation using the selected method. "
        "Calculates lift, p-values, confidence intervals, and balance checks where applicable."
    )
    args_schema: Type[BaseModel] = StatisticalValidationInput

    def _run(self, dataset_id: str, method_selection_json: str, config_json: str) -> str:
        df = get_registered_dataframe(dataset_id)
        method_selection = json.loads(method_selection_json)
        config = json.loads(config_json)

        result = run_statistical_validation(
            df=df,
            method_selection=method_selection,
            config=config,
        )

        return json.dumps(result, indent=2)


class BusinessImpactTool(BaseTool):
    name: str = "business_impact_tool"
    description: str = (
        "Calculates expected value, incremental expected value, total incremental value, "
        "and whether treatment economics are financially positive."
    )
    args_schema: Type[BaseModel] = BusinessImpactInput

    def _run(
        self,
        statistical_result_json: str,
        business_value_per_success: float,
        intervention_cost_per_success: float = 0.0,
    ) -> str:
        statistical_result = json.loads(statistical_result_json)

        result = calculate_business_impact(
            statistical_result=statistical_result,
            business_value_per_success=business_value_per_success,
            intervention_cost_per_success=intervention_cost_per_success,
        )

        return json.dumps(result, indent=2)


class SegmentAnalysisTool(BaseTool):
    name: str = "segment_analysis_tool"
    description: str = (
        "Runs segment and intersectional segment analysis to identify heterogeneous "
        "treatment effects and segment-level opportunities."
    )
    args_schema: Type[BaseModel] = SegmentAnalysisInput

    def _run(self, dataset_id: str, config_json: str) -> str:
        df = get_registered_dataframe(dataset_id)
        config = json.loads(config_json)

        segment_cols = config.get("segment_cols", [])

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

        combined_results = segment_results + intersectional_results
        summary = summarize_segment_results(combined_results)

        result = {
            "segment_results": combined_results,
            "segment_summary": summary,
        }

        return json.dumps(result, indent=2, default=str)


class LanguageGuardrailTool(BaseTool):
    name: str = "language_guardrail_tool"
    description: str = (
        "Scans and rewrites business language so claims do not exceed the approved evidence tier."
    )
    args_schema: Type[BaseModel] = LanguageGuardrailInput

    def _run(self, text: str, evidence_tier: str) -> str:
        scan = scan_for_blocked_language(
            text=text,
            evidence_tier=evidence_tier,
        )

        rewrite = rewrite_claim_language(
            text=text,
            evidence_tier=evidence_tier,
        )

        result = {
            "scan": scan,
            "rewrite": rewrite,
        }

        return json.dumps(result, indent=2)


def get_claimcheck_tools() -> List[Any]:
    """
    Return all ClaimCheck CrewAI tools.
    """
    return [
        SecurityGateTool(),
        DataProfilerTool(),
        MethodSelectorTool(),
        StatisticalValidationTool(),
        BusinessImpactTool(),
        SegmentAnalysisTool(),
        LanguageGuardrailTool(),
    ]
