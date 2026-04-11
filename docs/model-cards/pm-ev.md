# Model Card: pm-ev AI Tools

This model card describes the components within the `pm-ev` module of PDA Platform. It is intended for project controls professionals, governance teams, and others who need to understand what is deterministic and what is AI-generated within the earned value toolchain.

---

## Model Details

- **Earned Value calculations**: fully deterministic. No AI is involved in computing SPI, CPI, SV, CV, EAC, ETC, VAC, or TCPI. Calculations follow the ANSI/EIA-748 standard for Earned Value Management and produce the same result for the same inputs on every run.
- **Interpretation text**: generated using Anthropic Claude accessed via the Anthropic API (`ANTHROPIC_API_KEY`). The model is pinned in the `agent-task-planning` package — see `packages/agent-task-planning/pyproject.toml` for the current pin.
- **HTML dashboard**: generated programmatically from computed metrics. No AI is involved in dashboard construction.
- **Integration layer**: the `agent-task-planning` package provides provider abstraction and structured output handling for the interpretation step.

---

## Intended Use

The `pm-ev` module is designed for project controls professionals and governance teams tracking cost and schedule performance against baseline. The primary use cases are:

- **Monthly cost and schedule performance reporting**: computing the full suite of EVM metrics from user-supplied PV, EV, AC, and BAC values and generating a plain-English interpretation of what the metrics indicate.
- **Board and programme control dashboards**: the HTML dashboard output is suitable for distribution to governance audiences following practitioner review.
- **Gate review supporting evidence**: EVM metric outputs provide quantitative evidence of cost and schedule performance for gate review packs.

All interpretation text is advisory. The mathematical metrics are precise given correct inputs; it is the interpretation of those metrics — and the validity of the inputs themselves — that requires professional judgement.

---

## Out-of-Scope Uses

The following uses are outside the intended scope of these tools and should be avoided:

- **Treating EAC projections as certainties**: EAC is a forecast based on current performance trends continuing. It is not a guarantee. Projections should be presented as estimates with associated uncertainty.
- **Sole basis for programme termination or major scope decisions**: EVM metrics are one input to a broader picture of delivery health. They do not capture stakeholder confidence, political risk, supplier health, or qualitative programme factors.
- **Bypassing practitioner review of the HTML dashboard**: the dashboard is a tool output, not a finished governance product. It should be reviewed before distribution to boards or senior stakeholders.

---

## Training Data

Not applicable for EVM calculations — these are mathematical operations with no training component. For interpretation text, PDA Platform uses a pre-trained foundation model (Anthropic Claude) via API. No fine-tuning or additional training has been performed using project delivery data. The model's training data, training methodology, and data governance are Anthropic's responsibility and are documented in Anthropic's published model cards.

---

## Evaluation

### EVM Metric Accuracy

EVM metrics (SPI, CPI, SV, CV, EAC, ETC, VAC, TCPI) are deterministic given correct inputs. The platform applies the standard ANSI/EIA-748 formulae:

| Metric | Formula |
|---|---|
| SPI | EV / PV |
| CPI | EV / AC |
| SV | EV - PV |
| CV | EV - AC |
| EAC (method 1) | BAC / CPI |
| EAC (method 2) | AC + (BAC - EV) |
| EAC (method 3) | AC + (BAC - EV) / CPI |
| ETC | EAC - AC |
| VAC | BAC - EAC |
| TCPI | (BAC - EV) / (BAC - AC) |

All three EAC methods are returned. Method 1 (BAC/CPI) assumes current cost efficiency continues. Method 2 (AC + remaining budget) assumes remaining work is completed at budget. Method 3 applies current CPI to remaining work — generally the most conservative projection for projects running over budget.

### Confidence Calibration

EVM metric values are mathematically certain given the inputs provided. The only source of uncertainty is input quality — specifically:

1. **Whether Earned Value has been correctly computed**: EV should reflect physical % complete of deliverables, not time elapsed or spend elapsed. If teams are measuring % complete based on time or spend rather than deliverables completed, CPI and SPI will be systematically misleading. The platform accepts EV as a direct user input and does not independently verify how it was computed.
2. **Whether the BAC reflects current approved scope**: if scope has changed without a corresponding BAC adjustment, all metrics referencing BAC will be unreliable.

Users should confirm the measurement basis for EV before relying on CPI and SPI trends for governance reporting.

---

## Limitations

- **Garbage-in, garbage-out for EV measurement**: the mathematical precision of EVM outputs is only as reliable as the physical progress measurement underlying EV. Inaccurate EV input is the most common source of misleading EVM outputs in practice.
- **EAC assumes current CPI continues**: EAC projections based on CPI (method 1 and method 3) assume that cost efficiency for completed work predicts efficiency for remaining work. This may overstate risk on projects where early inefficiency is expected to improve, and understate risk on projects where performance is deteriorating.
- **TCPI values above 1.2 are rarely achievable**: a TCPI significantly above 1.0 means the remaining work must be completed at substantially better efficiency than work to date. Values above 1.2 are mathematically real but practically indicate a project in serious difficulty — they should be flagged for SRO attention rather than treated as a performance target.
- **No automatic EV computation from schedule data**: the platform does not compute EV from task-level schedule data. Users must supply EV as a direct input. Teams without a formal EVM system must ensure they are computing EV consistently before using this tool.
- **API dependency for interpretation**: interpretation text requires a valid `ANTHROPIC_API_KEY`. If the key is absent, metric calculations are still performed and returned, but plain-English interpretation is unavailable.

---

## Failure Modes

- **Dual negative performance (AC > EV and PV > EV)**: projects that are simultaneously over budget and behind schedule will produce high TCPI values. These are correct signals of serious delivery risk, not errors. Teams should not dismiss them as calculation anomalies.
- **CPI exactly equal to 1.0**: EAC method 1 (BAC/CPI) returns BAC when CPI = 1.0 exactly. This is the correct mathematical result and indicates on-budget performance — it is not an error if it appears suspiciously round.
- **Zero or missing BAC**: a BAC of zero causes division errors in CPI-based EAC methods. The tool validates and rejects zero BAC inputs. Missing BAC must be supplied before the tool can run.
- **Very small PV**: SPI values become unreliable when PV is very small relative to EV (common in early project phases before significant planned value has been earned). Treat SPI with caution in the first weeks of a project.

---

## Ethical Considerations

- **No PII processed**: the tools process financial and schedule metrics only. No personal data or named individuals should be submitted. Responsibility for data minimisation rests with the user.
- **Advisory interpretation**: AI-generated interpretation text is explicitly advisory. The platform documentation consistently describes interpretation as requiring practitioner review before use in governance contexts.
- **Auditability**: EVM metrics and interpretation outputs stored in the AssuranceStore include the tool name, timestamp, project identifier, and input values used, enabling retrospective audit of what data was submitted and what outputs were produced.

---

## Human Oversight Requirements

EVM metrics should be reviewed by a qualified project controls professional before being presented to governance forums. The reviewing professional should:

- Confirm the measurement basis for EV (deliverables-based, not time- or spend-based)
- Confirm that BAC reflects current approved scope
- Apply professional judgement about whether CPI/SPI trends warrant the trajectory the metrics suggest
- Review the AI-generated interpretation text for accuracy and appropriate framing before including it in governance documents

The HTML dashboard is suitable for board distribution after this practitioner review step. It should not be distributed directly from tool output without review.

---

## Appropriate Use Boundary

`pm-ev` is suitable for: computing the full EVM metric suite from user-supplied inputs; generating plain-English interpretation of EVM performance for practitioner review; producing HTML dashboards for distribution following review; providing quantitative evidence of cost and schedule performance for gate review packs.

`pm-ev` is not suitable as: the sole source of truth for major scope or investment decisions; a replacement for a formal Earned Value Management System where one is required; an automatic EV calculator that bypasses the need for teams to measure physical progress correctly.

---

## Caveats

- Deployments on Render's free tier may experience cold start latency of several seconds on the first request after a period of inactivity. This affects response time but not the mathematical outputs, which are computed locally.
- EVM is most meaningful when applied consistently across a project's lifecycle. One-off use for a single reporting period without historical context limits the analytical value of trend-based metrics like CPI trajectory.
- The three EAC methods will produce different values unless CPI = 1.0 exactly. All three are returned so that practitioners can apply the most appropriate method for their context. Method selection should be documented in the project's controls baseline.
