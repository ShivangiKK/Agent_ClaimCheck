# ClaimCheck Architecture

ClaimCheck is an agentic AI workflow for evidence-governed business claim review.

The system reviews whether a stakeholder claim is statistically supported, commercially justified, and safe to communicate before it enters an executive report, dashboard, or slide deck.

## Core Architecture

```text
User Claim + Dataset
        ↓
Lovelace
Security and Control Agent
        ↓
Toulmin
Claim Structuring Agent
        ↓
Fisher
Method Selection Agent
        ↓
Deterministic Evidence Engine
Data Profiler · Stats Engine · Business Impact Engine · Language Guardrail · Audit Logger
        ↓
Wald
Validity Risk Agent
        ↓
Minto
Brief Builder Agent
        ↓
Playfair
Artifact Generation Agent
        ↓
Word Report · PowerPoint Deck · JSON Evidence Packet · Audit Log
```

## Design Principle

ClaimCheck separates interpretation from validation.

LLM agents are used for:

- interpreting stakeholder language;
- structuring claims;
- explaining method choices;
- writing executive-facing narratives.

Deterministic tools are used for:

- data profiling;
- statistical tests;
- p-values and confidence intervals;
- treatment/control balance checks;
- business-impact calculations;
- evidence-tier assignment;
- language guardrails;
- audit logging;
- artifact generation.

This design prevents the LLM from inventing statistical evidence or overstating unsupported claims.

## Workflow Stages

### 1. Input Security

**Agent:** Lovelace  
**Purpose:** Screen claim text, column names, and sample rows before LLM exposure.

Lovelace checks for prompt injection, suspicious instructions, system-prompt references, and unsafe content. If risk is detected, the workflow stops and routes to human review.

### 2. Claim Structuring

**Agent:** Toulmin  
**Purpose:** Convert messy stakeholder language into a structured analytical claim.

Example input:

```text
The campaign drove purchases and should be rolled out broadly.
```

Example structured output:

```json
{
  "claim_type": "prescriptive_recommendation",
  "requested_evidence_strength": "causal",
  "outcome": "purchase",
  "treatment": "campaign exposure",
  "decision": "broad rollout"
}
```

### 3. Method Selection

**Agent:** Fisher  
**Purpose:** Select the correct method family from the method registry.

Fisher determines whether the claim should be routed to:

- two-proportion test;
- two-sample t-test;
- predictive/driver review;
- descriptive-only review;
- pre/post analysis;
- difference-in-differences;
- regression-adjusted review;
- human review.

The prototype currently implements the treatment-control pathways and routes unsupported methods safely.

### 4. Deterministic Evidence Engine

The deterministic evidence engine performs reproducible analysis.

Core tools:

| Tool | Purpose |
|---|---|
| Data Profiler | Inspects dataset shape, columns, missingness, outcome type, treatment structure |
| Method Registry | Stores approved method families and prototype support status |
| Stats Engine | Runs statistical validation |
| Balance Checker | Tests whether treatment/control groups are balanced on covariates |
| Segment Review Tool | Checks heterogeneous effects across configured segments |
| Business Impact Engine | Calculates expected value and rollout economics |
| Evidence Tier Router | Assigns Descriptive, Predictive, Suggestive, Causal, or Decision-Ready evidence tier |
| Language Guardrail | Blocks unsupported causal or decision-ready language |
| Audit Logger | Records claim, method, evidence, review status, and output paths |

### 5. Validity Risk Review

**Agent:** Wald  
**Purpose:** Review what the evidence does not prove.

Wald checks:

- whether causal language is supported;
- whether business impact is positive or negative;
- whether segment findings conflict with the overall result;
- whether the evidence tier matches the requested claim strength;
- whether human review is required.

### 6. Business Brief Generation

**Agent:** Minto  
**Purpose:** Convert validated evidence into executive-facing language.

Minto receives a structured evidence packet and writes:

- executive answer;
- evidence summary;
- business-impact explanation;
- segment or driver insight;
- governance status;
- recommended next step.

Minto is constrained by the language guardrail. It cannot use causal or decision-ready wording unless the evidence tier permits it.

### 7. Artifact Generation

**Agent:** Playfair  
**Purpose:** Generate shareable business artifacts.

Outputs include:

- Word evidence report;
- PowerPoint executive deck;
- JSON evidence packet;
- brief text;
- charts;
- audit log;
- ZIP bundle.

## Memory Design

ClaimCheck uses three memory layers.

| Memory type | Prototype implementation | Production implementation |
|---|---|---|
| Short-term memory | Current notebook/session variables | CrewAI task context |
| Run memory | JSON audit logs and evidence packets | Database of completed reviews |
| Long-term memory | Planned | Vector store or warehouse table of prior claims, metric definitions, and approved language rules |

This allows a user to rework a claim, change assumptions, or compare the current review against previous runs.

## Human-in-the-Loop Design

ClaimCheck uses constrained autonomy. It can complete first-pass analytical review, but it routes exceptions to a human reviewer.

Human review is triggered when:

- security checks fail;
- required fields are missing;
- method is unsupported;
- causal claim lacks valid design;
- business impact is negative;
- segment opportunity conflicts with overall rollout economics;
- requested claim strength exceeds evidence tier;
- generated narrative violates language permissions.

## Why This Is Agentic

ClaimCheck is agentic because it:

- decomposes a business workflow into specialized roles;
- uses tools to act on data;
- maintains workflow state;
- routes conditionally based on evidence and risk;
- uses guardrails and human handoff;
- generates final artifacts;
- evaluates its own routing and language safety behavior.

It is not a simple chatbot or one-shot report generator. It is an evidence-governed analytical review workflow.
