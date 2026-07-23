"""
ClaimCheck CrewAI Orchestration

This file defines the planned CrewAI structure for ClaimCheck.

The current Streamlit app runs the deterministic workflow directly.
This file documents and prepares the agent orchestration layer.

Run later with:
python crew.py
"""

from typing import Any, Dict


try:
    from crewai import Agent, Crew, Process, Task
except ImportError:
    Agent = None
    Crew = None
    Process = None
    Task = None


def crewai_available() -> bool:
    """Check whether CrewAI is installed."""
    return all(item is not None for item in [Agent, Crew, Process, Task])


def build_claimcheck_agents() -> Dict[str, Any]:
    """
    Build ClaimCheck agent definitions.

    These agents map to the documented workflow:
    Lovelace → Toulmin → Fisher → Deterministic Tools → Wald → Minto → Playfair
    """
    if not crewai_available():
        raise ImportError(
            "CrewAI is not installed. Install dependencies with: pip install -r requirements.txt"
        )

    lovelace = Agent(
        role="AI Safety and Workflow Control Lead",
        goal="Screen user claims, dataset column names, and sample rows before LLM exposure.",
        backstory=(
            "You are Lovelace, the security and control agent for ClaimCheck. "
            "Your job is to prevent unsafe, adversarial, or suspicious inputs from "
            "entering the analytical workflow."
        ),
        verbose=True,
        allow_delegation=False,
    )

    toulmin = Agent(
        role="Senior Analyst, Claim Structuring",
        goal="Convert stakeholder language into a structured, testable analytical claim.",
        backstory=(
            "You are Toulmin, the claim structuring agent. You translate messy business "
            "claims into structured hypotheses, identify requested evidence strength, "
            "and flag missing context."
        ),
        verbose=True,
        allow_delegation=False,
    )

    fisher = Agent(
        role="Decision Scientist, Measurement Design",
        goal="Select the correct analytical method family from the approved method registry.",
        backstory=(
            "You are Fisher, the method selection agent. You determine whether a claim "
            "requires a two-proportion test, t-test, descriptive review, predictive review, "
            "or human escalation."
        ),
        verbose=True,
        allow_delegation=False,
    )

    wald = Agent(
        role="Senior Analyst, Risk and Measurement",
        goal="Detect overclaiming, missing evidence, negative business impact, and human-review triggers.",
        backstory=(
            "You are Wald, the validity risk agent. Your job is to examine what the evidence "
            "does not prove and prevent unsupported analytical claims from becoming decisions."
        ),
        verbose=True,
        allow_delegation=False,
    )

    minto = Agent(
        role="Director, Analytics Communication",
        goal="Convert validated evidence into concise executive-facing language.",
        backstory=(
            "You are Minto, the brief builder agent. You write clear executive summaries "
            "using only validated evidence and approved language."
        ),
        verbose=True,
        allow_delegation=False,
    )

    playfair = Agent(
        role="Analytics Artifact and Visualization Lead",
        goal="Prepare structured outputs for charts, reports, decks, evidence packets, and audit logs.",
        backstory=(
            "You are Playfair, the artifact generation agent. You turn validated evidence "
            "and approved narrative into business-ready artifacts."
        ),
        verbose=True,
        allow_delegation=False,
    )

    return {
        "lovelace": lovelace,
        "toulmin": toulmin,
        "fisher": fisher,
        "wald": wald,
        "minto": minto,
        "playfair": playfair,
    }


def build_claimcheck_tasks(agents: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build ClaimCheck CrewAI task definitions.

    The deterministic Python tools remain the source of truth for calculations.
    CrewAI agents are used for orchestration, interpretation, and communication.
    """
    if not crewai_available():
        raise ImportError(
            "CrewAI is not installed. Install dependencies with: pip install -r requirements.txt"
        )

    security_task = Task(
        description=(
            "Review the submitted claim and dataset metadata for security risk. "
            "Confirm whether the workflow can continue or should halt for human review. "
            "Do not perform statistical analysis."
        ),
        expected_output=(
            "A structured security decision with status, risk explanation, and next action."
        ),
        agent=agents["lovelace"],
    )

    claim_structuring_task = Task(
        description=(
            "Convert the stakeholder claim into a structured analytical claim. "
            "Identify claim type, requested evidence strength, required fields, "
            "and missing context."
        ),
        expected_output=(
            "A structured claim profile including claim type, evidence strength, "
            "required fields, and missing information flags."
        ),
        agent=agents["toulmin"],
    )

    method_selection_task = Task(
        description=(
            "Review the structured claim and dataset profile. Select the appropriate "
            "method family from the approved method registry. Route unsupported methods "
            "to human review."
        ),
        expected_output=(
            "A method-selection decision including selected method, runnable status, "
            "reason, and review requirement."
        ),
        agent=agents["fisher"],
    )

    validity_review_task = Task(
        description=(
            "Review deterministic statistical outputs, business-impact outputs, and "
            "segment results. Identify overclaiming, negative economics, evidence gaps, "
            "and human-review triggers."
        ),
        expected_output=(
            "A validity review including evidence tier, risk flags, permitted language, "
            "and human-review reasons."
        ),
        agent=agents["wald"],
    )

    brief_builder_task = Task(
        description=(
            "Write an executive-facing summary using only validated evidence. "
            "Do not invent numbers. Do not use causal or decision-ready language unless "
            "the evidence tier permits it."
        ),
        expected_output=(
            "A concise executive brief with verdict, evidence summary, business impact, "
            "segment insight, and recommended next step."
        ),
        agent=agents["minto"],
    )

    artifact_task = Task(
        description=(
            "Prepare structured artifact instructions for charts, report, deck, JSON evidence "
            "packet, and audit log. Ensure artifact language follows the approved evidence tier."
        ),
        expected_output=(
            "A structured artifact plan listing required charts, report sections, deck slides, "
            "JSON outputs, and audit fields."
        ),
        agent=agents["playfair"],
    )

    return {
        "security_task": security_task,
        "claim_structuring_task": claim_structuring_task,
        "method_selection_task": method_selection_task,
        "validity_review_task": validity_review_task,
        "brief_builder_task": brief_builder_task,
        "artifact_task": artifact_task,
    }


def build_claimcheck_crew() -> Any:
    """
    Build the ClaimCheck Crew.

    Note:
    The production architecture should use CrewAI Flow for state, branching,
    and deterministic tool execution. This Crew definition documents the agent
    roles and task order for the current prototype.
    """
    if not crewai_available():
        raise ImportError(
            "CrewAI is not installed. Install dependencies with: pip install -r requirements.txt"
        )

    agents = build_claimcheck_agents()
    tasks = build_claimcheck_tasks(agents)

    crew = Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        process=Process.sequential,
        verbose=True,
    )

    return crew


if __name__ == "__main__":
    if not crewai_available():
        print("CrewAI is not installed. Run: pip install -r requirements.txt")
    else:
        crew = build_claimcheck_crew()
        print("ClaimCheck CrewAI workflow initialized.")
        print(crew)
