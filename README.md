# ClaimCheck: Evidence-Governed Business Claim Review Agent

ClaimCheck is an agentic AI workflow that reviews whether business claims are supported by data before they enter executive reports, dashboards, or slide decks.

It is designed for business analysts, product managers, analytics managers, and decision scientists who need to validate claims such as:

> “The campaign drove purchases and should be rolled out broadly.”

ClaimCheck separates three questions that are often conflated in business reporting:

1. Did the data show statistical lift?
2. Is the business action economically justified?
3. Is the claim safe to communicate in executive language?

## Why ClaimCheck?

Generic LLMs can generate polished reports from uploaded data, but they may overstate causal findings, ignore business economics, or turn weak evidence into confident recommendations.

ClaimCheck uses LLM agents for interpretation and communication, while deterministic tools handle profiling, statistical validation, business-impact calculation, language guardrails, artifact generation, and audit logging.

The goal is not just to summarize data. The goal is to prevent unsupported business claims from becoming executive decisions.

## Agentic Workflow

```text
Lovelace → Toulmin → Fisher → Deterministic Tools → Wald → Minto → Playfair
```

| Agent | Enterprise role | Function |
|---|---|---|
| Lovelace | AI Safety and Workflow Control Lead | Screens inputs before LLM exposure |
| Toulmin | Senior Analyst, Claim Structuring | Converts stakeholder claims into structured hypotheses |
| Fisher | Decision Scientist, Measurement Design | Selects the appropriate method family from the approved method registry |
| Wald | Senior Analyst, Risk and Measurement | Reviews missing evidence, overclaiming, business risk, and human-review triggers |
| Minto | Director, Analytics Communication | Converts validated evidence into executive-facing narrative |
| Playfair | Analytics Artifact and Visualization Lead | Produces charts, Word reports, PowerPoint decks, JSON outputs, and audit bundles |

## What ClaimCheck Does

The current prototype supports:

- treatment-control campaign review;
- binary outcome testing using two-proportion tests;
- treatment/control balance checks;
- segment-level treatment-effect review;
- business-impact calculation;
- evidence-tier assignment;
- tier-locked language guardrails;
- human-review routing;
- audit logging;
- Word and PowerPoint artifact generation;
- evaluation harnesses for method selection and language safety.

## Benchmark Case

The first benchmark uses a GameFun treatment-control campaign dataset.

Expected benchmark pattern:

- treatment and control are balanced on observable covariates;
- purchase lift is positive and statistically significant;
- broad rollout is not automatically justified if campaign economics are unfavorable;
- segment heterogeneity matters;
- targeted review may be more appropriate than broad rollout.

ClaimCheck recovered this pattern and routed the broad rollout recommendation to human review.

## Evaluation Snapshot

| Metric | Prototype result |
|---|---:|
| Method-selection accuracy | 100% |
| Claim-type accuracy | 66.7% |
| Human-review routing accuracy | 100% |
| Language-safety accuracy before guardrail update | 80% |
| Language-safety accuracy after guardrail update | 100% |

The current weakest layer is claim-type classification. This is expected in the prototype because business language is ambiguous. In the CrewAI version, this layer is handled by the Claim Structuring Agent, while deterministic tools continue to control validation, evidence tiers, and language safety.

## Repository Structure

```text
notebooks/        R&D notebook used to design and test the prototype
src/tools/        Deterministic tools for validation, safety, and artifact generation
src/agents/       CrewAI agent definitions, planned
docs/             Architecture, agent cards, and evaluation plan
outputs/          Generated reports, decks, audit logs, and evaluation artifacts
app.py            Streamlit demo entry point
crew.py           CrewAI orchestration entry point
```

## Status

This project is currently in prototype stage.

The Colab notebook contains the full R&D workflow. The GitHub repo is being modularized for:

- reusable deterministic tools;
- CrewAI orchestration;
- Streamlit demo deployment;
- documented agent roles and guardrails;
- evaluation and auditability.

## Next Steps

- Modularize the deterministic core into `src/tools/`.
- Add Streamlit demo for dataset upload, claim entry, column mapping, verdict display, and artifact download.
- Add CrewAI orchestration around the named agent workflow.
- Expand evaluation with additional business claim types and security tests.
