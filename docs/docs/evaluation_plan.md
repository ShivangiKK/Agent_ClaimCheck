# ClaimCheck Evaluation Plan

ClaimCheck is evaluated as an enterprise agentic AI workflow for evidence-governed business claim review.

The workflow being automated is the first-pass analytical review that happens before a claim enters an executive report, dashboard, or slide deck. The agent reviews whether a stakeholder claim is statistically supported, commercially justified, and safe to communicate.

Example claim:

> “The campaign drove purchases and should be rolled out broadly.”

ClaimCheck is designed to prevent a polished but unsupported analytical story from becoming an executive decision.

---

## 1. CrewAI Use-Case Quadrant

CrewAI’s use-case evaluation framework recommends assessing agentic systems along two dimensions: **complexity** and **precision**. Complexity considers the number of steps, interdependencies, conditional logic, and domain knowledge required. Precision considers the need for accuracy, structured outputs, reproducibility, and control over variation. According to CrewAI’s framework, high-complexity and high-precision use cases often require a combination of controlled flows, validation steps, and specialized agents rather than a single open-ended agent.  

ClaimCheck falls in the **High Complexity, High Precision** quadrant.

| Dimension | Score | Rationale |
|---|---:|---|
| Complexity | 8/10 | The workflow requires multiple dependent steps: input security, claim structuring, method selection, data profiling, statistical validation, business-impact calculation, evidence-tiering, language guardrails, human-review routing, brief generation, artifact generation, and audit logging. |
| Precision | 9/10 | The system must calculate p-values, lift, confidence intervals, expected value, evidence tiers, and language permissions reproducibly. Incorrect outputs could lead to unsupported business decisions. |

### Recommended Architecture

Because ClaimCheck is high-complexity and high-precision, the appropriate architecture is:

```text
CrewAI Flow for control, state, branching, and reliability
+
Specialized agents for claim interpretation, risk review, and communication
+
Deterministic Python tools for statistics, validation, business impact, and artifacts
```

This avoids the main risk of a single LLM agent: producing a fluent but unsupported business recommendation.

---

## 2. Agent Overview

ClaimCheck uses a named multi-agent workflow:

```text
Lovelace → Toulmin → Fisher → Deterministic Tools → Wald → Minto → Playfair
```

| Agent | Function | Responsibility |
|---|---|---|
| Lovelace | Security and Control | Screens inputs before LLM exposure |
| Toulmin | Claim Structuring | Converts stakeholder language into a structured analytical claim |
| Fisher | Method Selection | Selects the appropriate method family from the method registry |
| Deterministic Tools | Evidence Engine | Runs data profiling, statistics, balance checks, business-impact logic, and audit logging |
| Wald | Validity Risk | Detects overclaiming, missing evidence, segment conflict, and review triggers |
| Minto | Brief Builder | Generates executive-facing narrative from validated evidence |
| Playfair | Artifact Generation | Produces charts, reports, decks, JSON packets, and audit bundles |

### Key Design Choice

LLMs are used for interpretation and communication. Deterministic tools are used for calculation, evidence control, safety, and auditability.

The LLM is not trusted to calculate p-values, lift, confidence intervals, expected value, or evidence tiers.

---

## 3. Performance Evaluation

ClaimCheck is evaluated across four layers:

1. **Method-selection accuracy**
2. **Statistical correctness**
3. **Governance safety**
4. **Business usefulness**

### 3.1 Method-Selection Accuracy

The Method Selection Agent is evaluated against labeled business claims.

Example test cases include:

| Claim | Expected method |
|---|---|
| “The campaign drove purchases.” | Two-proportion test |
| “Variant B increased average revenue.” | Two-sample t-test |
| “This churn score predicts which customers are likely to leave.” | Predictive/driver review |
| “Revenue increased by 12% last month.” | Descriptive-only review |
| “Revenue dropped after launch, so the launch caused the decline.” | Pre/post review with human escalation |

Current prototype result:

| Metric | Result |
|---|---:|
| Method-selection accuracy | 100% |
| Method-selection precision | 100% on the labeled prototype set |
| Method-selection recall | 100% on the labeled prototype set |

This result is based on a small synthetic evaluation set. It is useful as a unit test, not as proof of full production generalization.

### 3.2 Claim-Type Accuracy

The claim-type classifier identifies whether a claim is descriptive, predictive, causal, prescriptive, comparative, or decision-ready.

Current prototype result:

| Metric | Result |
|---|---:|
| Claim-type accuracy | 66.7% |

This is the weakest current layer. The failure cases show that business language is ambiguous. For example, “revenue increased” may be descriptive in one context but causal in another.

### Improvement Plan

In the CrewAI version, Toulmin handles claim structuring with LLM support and structured output constraints. Deterministic tools still control method selection, evidence tiering, and language safety.

---

## 4. Statistical Correctness

The statistical engine is deterministic.

For the GameFun treatment-control benchmark, ClaimCheck checks:

- treatment/control structure;
- binary outcome type;
- treatment/control balance on observable covariates;
- purchase lift;
- p-value;
- confidence interval;
- segment-level treatment effects;
- expected value per customer;
- financial viability of broad rollout.

The benchmark pattern expected from human analysis is:

- treatment and control are balanced;
- purchase lift is positive and statistically significant;
- broad rollout is not automatically justified if economics are unfavorable;
- segment heterogeneity matters;
- targeted review may be more appropriate than broad rollout.

ClaimCheck recovered this pattern and routed the broad rollout recommendation to human review.

---

## 5. Reliability Evaluation

Reliability means that the system should produce stable, reproducible outputs for the same claim, dataset, configuration, and business assumptions.

ClaimCheck improves reliability through:

- deterministic statistical functions;
- method registry;
- dataset hash;
- structured configuration;
- JSON evidence packet;
- audit log;
- reproducible artifact generation;
- human-review routing for unsupported or ambiguous cases.

### Reliability Tests

| Reliability test | Expected behavior |
|---|---|
| Same dataset and same claim | Same statistical result and evidence tier |
| Same dataset and different claim strength | Same statistics, different language permissions if needed |
| Missing treatment column | Route to descriptive/review pathway |
| Unsupported method | Route to human review |
| Negative business impact | Block broad rollout recommendation |
| Positive segment with negative overall impact | Route to human review |

---

## 6. Safety Evaluation

Safety is evaluated through language control and evidence-tier enforcement.

The core safety risk is overclaiming. A generic LLM may turn weak or suggestive evidence into causal or decision-ready language.

ClaimCheck uses evidence tiers:

| Evidence tier | Meaning |
|---|---|
| Descriptive | Summarizes what happened |
| Predictive | Supports prediction or risk ranking |
| Suggestive | Shows association or directional evidence |
| Causal | Supports causal treatment-effect language |
| Decision-Ready | Supports action language after business and governance checks |

### Language-Safety Results

| Metric | Result |
|---|---:|
| Language-safety accuracy before guardrail update | 80% |
| Language-safety accuracy after guardrail update | 100% |

The evaluation found one failed safety case: the system did not initially block “proves” and “drove” under the Suggestive evidence tier. The guardrail was updated, and the evaluation was rerun successfully.

This demonstrates a review cycle:

```text
Evaluate → detect failure → update guardrail → rerun evaluation → record improvement
```

---

## 7. Security Evaluation

Security focuses on preventing unsafe or adversarial inputs from reaching LLM agents.

The Lovelace Security and Control Agent screens:

- claim text;
- dataset column names;
- sample rows;
- suspicious prompt-injection language;
- system-prompt references;
- unsafe code patterns.

Examples of blocked patterns:

```text
ignore previous instructions
system prompt
developer message
drop table
<script
eval(
exec(
reveal hidden prompt
```

### Security Metrics

| Metric | Definition |
|---|---|
| Injection detection rate | Share of known malicious prompts correctly blocked |
| False positive rate | Share of benign claims incorrectly blocked |
| Security logging completeness | Whether triggered patterns and actions are logged |
| LLM exposure control | Whether unsafe inputs are stopped before LLM agents run |

### Current Status

The security gate is planned as a deterministic module in `src/tools/security_gate.py`. It will be evaluated with benign and adversarial claims before the Streamlit demo is finalized.

---

## 8. Business Usefulness Evaluation

The business usefulness test asks whether ClaimCheck helps a stakeholder make a better decision.

For the GameFun benchmark, the value is that ClaimCheck separates:

1. **Statistical lift:** the campaign increased purchase probability.
2. **Business value:** broad rollout is not financially attractive under current assumptions.
3. **Governance:** causal language is allowed, but broad rollout recommendation language is not decision-ready.

This is the core product value:

> ClaimCheck prevents a statistically true finding from becoming an unsupported executive recommendation.

### Business Outputs

ClaimCheck produces:

- executive verdict;
- evidence packet;
- segment insight;
- business-impact summary;
- human-review reasons;
- Word evidence report;
- PowerPoint executive deck;
- audit log.

---

## 9. Product Manager Recommendations

If advising the product manager building ClaimCheck, the highest-priority recommendations are:

### 1. Narrow the initial wedge

Start with a focused use case:

```text
Marketing and product experiment review
```

This is where treatment/control analysis, rollout decisions, and executive reporting are common.

### 2. Do not position it as a generic EDA agent

Generic EDA agents are easy to build and easy to replace. ClaimCheck should own the more valuable workflow:

```text
Can this business claim safely go into a leadership deck?
```

### 3. Add integrations only after the core validation workflow works

Near-term integrations:

- CSV/Excel upload;
- Google Sheets;
- PowerPoint export;
- Word export.

Later enterprise integrations:

- Tableau;
- Power BI;
- Looker;
- Snowflake;
- BigQuery;
- Databricks;
- Slack or Teams approval workflows.

### 4. Make human review a feature, not a weakness

ClaimCheck should not claim full autonomy. The strongest enterprise positioning is:

```text
Autonomous first-pass review with human escalation for high-risk claims.
```

### 5. Improve claim-type classification

The weakest prototype layer is claim-type classification. The next product improvement should be structured LLM claim framing with deterministic validation.

### 6. Add organization-level memory

Production ClaimCheck should remember:

- prior reviewed claims;
- approved metric definitions;
- company-specific business assumptions;
- prior language decisions;
- human override history.

---

## 10. Willingness to Pay

ClaimCheck creates value by reducing senior analyst review time, improving decision quality, and preventing unsupported claims from reaching leadership.

### Recommended Pricing

| Customer type | Suggested pricing | Rationale |
|---|---:|---|
| Individual analyst | $20-$50/month | Comparable to productivity tools; useful for solo analysis and artifact generation |
| Team plan | $25-$75/user/month | Supports analyst teams, product teams, and marketing analytics teams |
| Enterprise plan | $30,000-$150,000/year | Includes governance, audit logs, SSO, connectors, templates, and admin controls |

### Why someone would pay

A company would pay if ClaimCheck can:

- save senior analyst review time;
- reduce bad rollout decisions;
- standardize analytical review;
- improve executive reporting quality;
- maintain audit trails;
- reduce overclaiming risk.

---

## 11. Deployment Cost Estimate

Actual deployment cost depends on model choice, data volume, artifact generation frequency, hosting provider, storage, and security requirements.

The estimates below assume a web app with file upload, deterministic Python tools, occasional LLM calls for claim framing and brief generation, artifact generation, and audit storage.

| Scale | Estimated monthly cost | Cost drivers |
|---|---:|---|
| 1 user | $5-$30/month | Streamlit hosting, light LLM usage, file storage |
| 1,000 users | $1,000-$8,000/month | app hosting, concurrent sessions, LLM calls, storage, logs, monitoring |
| 1 million users | $100,000+/month | autoscaling infrastructure, queueing, model routing, storage, observability, security, enterprise support |

### Cost-control strategies

- Use deterministic tools for statistics instead of LLM calls.
- Cache evidence packets and generated artifacts.
- Use smaller models for claim framing and brief drafting.
- Route only high-value narrative tasks to LLMs.
- Store audit logs cheaply in object storage or warehouse tables.
- Use batch processing for large teams.

---

## 12. Limitations

Current prototype limitations:

- claim-type classification is still rule-based and imperfect;
- only selected method families are implemented;
- security gate is planned but not yet fully evaluated;
- Streamlit and CrewAI orchestration are not yet complete;
- long-term vector memory is planned, not implemented;
- report and deck generation currently rely on deterministic outputs and template logic, with LLM narrative integration planned.

These limitations are acceptable for a prototype because the system explicitly routes unsupported or ambiguous cases to human review instead of pretending to be fully autonomous.

---

## 13. Final Evaluation Summary

ClaimCheck is a strong candidate for an enterprise agent workflow because it automates a repeated, high-value analytical review process.

It is stronger than a generic data-summary chatbot because it adds:

- method selection;
- statistical validation;
- business-impact logic;
- evidence-tiering;
- language safety;
- human-review routing;
- artifact generation;
- auditability.

The current prototype demonstrates the core workflow on a treatment-control campaign benchmark. The next version should prioritize CrewAI Flow orchestration, Streamlit demo deployment, security testing, and broader claim-type coverage.
