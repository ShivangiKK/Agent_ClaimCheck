# ClaimCheck Agent Cards

ClaimCheck uses role-based agents with explicit scope, tool access, guardrails, and handoff rules. The goal is to keep the workflow agentic without allowing the LLM to make unsupported analytical or business claims.

## Agent Flow

```text
Lovelace → Toulmin → Fisher → Deterministic Tools → Wald → Minto → Playfair
```

| Agent | Function | Primary responsibility |
|---|---|---|
| Lovelace | Security and Control | Screen inputs before LLM exposure |
| Toulmin | Claim Structuring | Convert stakeholder language into a testable claim |
| Fisher | Method Selection | Select the appropriate analytical pathway |
| Deterministic Tools | Evidence Engine | Profile data, run statistics, calculate business impact |
| Wald | Validity Risk | Detect overclaiming, weak evidence, and review triggers |
| Minto | Brief Builder | Generate executive-facing narrative from validated evidence |
| Playfair | Artifact Generation | Produce charts, reports, decks, JSON, and audit bundles |

---

## 1. Lovelace — Security and Control Agent

**Enterprise role:** AI Safety and Workflow Control Lead  
**Inspired by:** Ada Lovelace, for early computational logic and conditional branching.

### Mission

Prevent unsafe or adversarial inputs from entering the agent workflow.

### Responsibilities

- Scan the user claim, column names, and sample rows.
- Detect prompt-injection patterns or suspicious instructions.
- Halt the workflow before LLM exposure if risk is detected.
- Log security decisions for auditability.

### Inputs

- User-submitted claim
- Dataset column names
- Sample rows
- File metadata

### Outputs

- `security_passed`
- `triggered_patterns`
- `action`
- `human_review_required`

### Guardrails

- Unsafe patterns halt the workflow.
- Security failures are logged.
- LLM agents do not receive the input until Lovelace clears it.

### Human handoff

Triggered when the input contains prompt-injection language, suspicious code, system-prompt references, or requests to ignore instructions.

### Success metrics

- Prompt-injection detection rate
- False positive rate on benign inputs
- Security decision logging completeness

---

## 2. Toulmin — Claim Structuring Agent

**Enterprise role:** Senior Analyst, Claim Structuring  
**Inspired by:** Stephen Toulmin’s model of argument structure: claim, grounds, warrant, backing, qualifier, and rebuttal.

### Mission

Turn messy stakeholder language into a structured analytical claim.

### Responsibilities

- Identify the business claim.
- Classify the claim type.
- Identify requested evidence strength.
- Extract required analytical fields.
- Flag missing context before method selection.

### Inputs

- User claim
- Decision context
- Dataset metadata
- Business assumptions

### Outputs

- `structured_claim`
- `claim_type`
- `requested_evidence_strength`
- `required_fields`
- `missing_information_flags`

### Guardrails

- Cannot invent missing business assumptions.
- Cannot upgrade a claim to causal without supporting structure.
- Must flag missing outcome, treatment, time, segment, or value assumptions.

### Human handoff

Triggered when the claim cannot be made testable, the decision context is missing, or the requested evidence strength is ambiguous.

### Success metrics

- Hypothesis completeness rate
- Claim-type classification accuracy
- Missing-field detection rate

---

## 3. Fisher — Method Selection Agent

**Enterprise role:** Decision Scientist, Measurement Design  
**Inspired by:** Ronald Fisher’s work on experimental design and statistical inference.

### Mission

Select the correct analytical pathway from the approved method registry.

### Responsibilities

- Review the structured claim and dataset profile.
- Select the appropriate method family.
- Determine whether the method is runnable in the prototype.
- Route unsupported or ambiguous cases to review.

### Inputs

- Structured claim
- Dataset profile
- Outcome type
- Treatment/control structure
- Time fields
- Covariates
- Method registry

### Outputs

- `selected_method`
- `method_status`
- `auto_runnable`
- `method_reason`
- `human_review_required`

### Guardrails

- Only approved method families can be selected.
- Unsupported methods cannot be forced.
- Causal methods require valid experimental or quasi-experimental structure.

### Human handoff

Triggered when no approved method fits, the claim asks for causal evidence without a valid design, or the method is outside prototype scope.

### Success metrics

- Method-selection precision
- Method-selection recall
- Unsupported-method routing accuracy

---

## 4. Deterministic Tools — Evidence Engine

**Enterprise role:** Analytical Validation Layer

### Mission

Calculate the evidence. Do not interpret beyond the rules.

### Tools

- Data Profiler
- Method Registry
- Statistical Validation Engine
- Balance Checker
- Segment Review Tool
- Business Impact Engine
- Evidence Tier Router
- Language Guardrail
- Audit Logger

### Responsibilities

- Profile dataset structure.
- Validate configured columns.
- Run statistical tests.
- Calculate lift, p-values, confidence intervals, and balance checks.
- Estimate expected value and business impact.
- Assign evidence tier and language permissions.
- Produce audit logs.

### Guardrails

- LLMs do not calculate p-values, lift, confidence intervals, or business impact.
- Statistical outputs must be reproducible.
- Evidence tier rules are deterministic.

### Success metrics

- Statistical correctness
- Reproducibility
- Audit-log completeness
- Business-impact calculation accuracy

---

## 5. Wald — Validity Risk Agent

**Enterprise role:** Senior Analyst, Risk and Measurement  
**Inspired by:** Abraham Wald, for reasoning from missing evidence and survivorship bias.

### Mission

Review what the evidence does not prove.

### Responsibilities

- Identify unsupported causal claims.
- Detect overclaiming and evidence gaps.
- Review negative business impact.
- Flag segment conflicts.
- Decide whether human review is required.

### Inputs

- Original claim
- Method selection output
- Dataset profile
- Statistical validation output
- Segment analysis
- Business impact output
- Evidence-tier rules

### Outputs

- `evidence_tier`
- `risk_flags`
- `language_permissions`
- `human_review_required`
- `review_reasons`

### Guardrails

- Evidence tier cannot be upgraded without deterministic support.
- Decision-ready language is blocked unless evidence and business-impact rules permit it.
- Segment opportunity cannot automatically override negative overall economics.

### Human handoff

Triggered when business impact is negative, causal support is weak, segment findings conflict with the overall result, or the evidence tier is below the requested claim strength.

### Success metrics

- Human-review routing accuracy
- Decision-language blocking accuracy
- Sensitivity to known risk patterns

---

## 6. Minto — Brief Builder Agent

**Enterprise role:** Director, Analytics Communication  
**Inspired by:** Barbara Minto’s Pyramid Principle for executive communication.

### Mission

Convert validated evidence into executive-ready business language.

### Responsibilities

- Generate the executive answer.
- Summarize evidence clearly.
- Explain business impact.
- Highlight segment or driver insights.
- State review status and next step.
- Respect evidence-tier language constraints.

### Inputs

- Evidence packet
- Evidence tier
- Language permissions
- Review reasons
- Audience type

### Outputs

- Executive answer
- Evidence summary
- Business-impact explanation
- Segment or driver insight
- Recommended next step

### Guardrails

- Cannot invent numbers.
- Cannot exceed the evidence tier.
- Cannot use causal verbs unless causal language is permitted.
- Cannot use decision-ready language unless permitted.

### Human handoff

Triggered when the stakeholder asks for stronger wording than the evidence allows or when the generated brief violates evidence-tier permissions.

### Success metrics

- Tier-locked compliance rate
- Hallucinated-number rate
- Executive-readability score

---

## 7. Playfair — Artifact Generation Agent

**Enterprise role:** Analytics Artifact and Visualization Lead  
**Inspired by:** William Playfair, creator of foundational business chart forms.

### Mission

Turn validated evidence and approved narrative into shareable business artifacts.

### Responsibilities

- Generate charts.
- Create Word evidence reports.
- Create PowerPoint executive decks.
- Save JSON evidence packets.
- Save audit logs.
- Package outputs into a downloadable bundle.

### Inputs

- ClaimCheck output
- Evidence packet
- Approved brief
- Chart-ready data
- Audit log

### Outputs

- Word evidence report
- PowerPoint executive deck
- JSON evidence packet
- Brief text
- Charts
- ZIP artifact bundle

### Guardrails

- Artifacts must cite deterministic outputs.
- Reports cannot include unapproved claims.
- Decks cannot show decision-ready language if not permitted.
- Chart values must come from validated outputs.

### Human handoff

Triggered when artifact generation fails, required narrative is missing, or generated content violates evidence-tier permissions.

### Success metrics

- Artifact completion rate
- Chart accuracy
- Report/deck consistency with evidence packet

---

## Design Principle

ClaimCheck uses LLM agents for interpretation and communication, but deterministic tools control evidence, calculation, safety, and auditability.

This prevents a polished but unsupported report from becoming an executive decision.
