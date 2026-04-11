# Portfolio Manager Guide — PDA Platform

## Who this guide is for

You oversee multiple major projects within a programme or across a department's portfolio. You are accountable to an investment committee, a Chief Digital and Information Officer, or a Departmental Investment Committee for the aggregate health of the portfolio — not just for any individual project within it. Your challenge is systemic: spotting patterns across projects, directing limited assurance resource where it is most needed, and presenting a credible portfolio picture to senior stakeholders.

This guide shows you how to use the PDA Platform to produce portfolio-level analysis. You do not call tools directly. You describe what you need to Claude, which calls the tools and synthesises the results into portfolio-framed outputs.

---

## Setting up Claude for your role

Paste the Portfolio Manager system prompt into Claude's **System Prompt** field before your first session. Copy it from `docs/prompts/role-system-prompts.md` — the section headed **Portfolio Manager**.

Once set, Claude will default to the portfolio lens: aggregate health distribution, systemic risks, cross-project comparisons, and a prioritised view of where to direct attention. Claude will avoid getting drawn into operational detail for individual projects unless you specifically ask for it.

For deeper cross-portfolio analysis, the most effective approach is to run the Full Gate Readiness Analysis research prompt (from `docs/prompts/research-prompts.md`) for each project in your portfolio in sequence, and then call `compare_project_health` to get the cross-portfolio comparison. This produces the richest portfolio picture.

---

## What the platform can do for you

- Produce a portfolio health rollup — DCA distribution, gate readiness ranking, benefits confidence by project — ready for presentation to an investment committee
- Compare projects across shared dimensions to identify which are performing well and which need intervention
- Detect systemic risks: shared suppliers, key individuals whose departure would affect multiple workstreams, common technology dependencies, and shared assumptions not stress-tested across the portfolio
- Map resource conflicts across the portfolio: when the same person or team is committed to multiple projects simultaneously and what that means for delivery risk
- Rank projects by composite delivery risk to prioritise where to direct your next assurance review
- Surface aggregate benefits confidence versus strategic targets — is the portfolio, taken as a whole, on track to deliver the benefits that justified the investment?
- Identify trends: are the same projects repeatedly amber or red? Is the portfolio improving or deteriorating over time?

---

## Your most useful tools

| Tool | What it does for you | When most useful |
|---|---|---|
| `get_portfolio_health` | Aggregates health across all projects — DCA distribution, overall portfolio confidence | Investment committee preparation, DIC submissions |
| `get_portfolio_gate_readiness` | Returns gate readiness position for all projects, ranked | Identifying which projects face gate risk in the next quarter |
| `get_portfolio_brm_overview` | Benefits confidence summary across the portfolio | Benefits review boards, strategic target tracking |
| `get_portfolio_armm_summary` | ARMM maturity distribution across the portfolio | Governance quality assessment, systemic assurance gaps |
| `get_portfolio_assumptions_risk` | Identifies assumptions shared across multiple projects that have not been stress-tested at portfolio level | Systemic risk identification, business case integrity |
| `get_portfolio_risks` | Returns the highest-severity risks across the portfolio, including those shared between projects | Portfolio-level risk reporting, systemic threat detection |
| `compare_project_health` | Side-by-side comparison of health metrics across selected projects | Cross-portfolio analysis, committee presentations |
| `get_portfolio_capacity` | Aggregates resource demand versus supply across the portfolio | Capacity planning, systemic resource risk |
| `detect_resource_conflicts` | Identifies named individuals or skill sets committed to multiple projects simultaneously | Dependency mapping, single points of failure |
| `get_critical_resources` | Returns the key individuals and skills whose absence would affect multiple projects | Key-person risk, succession planning |
| `get_risk_velocity` | Tracks risk acceleration by project — identifies which projects' risk profiles are deteriorating fastest | Assurance prioritisation, early warning |
| `detect_stale_risks` | Flags projects with stale risk registers — a governance quality indicator | ARMM compliance, assurance prioritisation |

---

## Your most useful research prompts

| Prompt | Purpose | When to use |
|---|---|---|
| Full Gate Readiness Analysis (Research Prompt 1) — run per project, then `compare_project_health` | Produces a comparable IPA-format assessment for each project, enabling true cross-portfolio comparison | Quarterly portfolio reviews, investment committee prep |

To run this at portfolio level: for each project, paste Research Prompt 1 with the relevant project ID substituted in, and save the output. After running across all projects, ask Claude: "Now compare the health of all the projects you have just assessed" — Claude will call `compare_project_health` and produce the cross-portfolio view.

---

## Worked examples

### Example 1: Investment committee portfolio presentation

**Scenario**

You have an investment committee presentation next week. You need to present the portfolio RAG to the committee, highlight which projects require specific attention, and give the committee a credible evidence-based picture rather than a summary of programme teams' self-assessments.

**What to ask Claude**

> I am presenting the portfolio RAG to the investment committee next week. Give me the full portfolio health picture — DCA distribution, gate readiness ranking, benefits confidence by project, and a cross-project comparison. I need to be able to say something specific about each project.

**What Claude does behind the scenes**

Claude calls four tools:

1. `get_portfolio_health()` — DCA distribution across the portfolio: how many projects are Green, Amber-Green, Amber, Amber-Red, Red
2. `get_portfolio_gate_readiness()` — gate readiness ranking across all projects, including which gates are upcoming in the next 90 days
3. `get_portfolio_brm_overview()` — benefits confidence by project, showing which projects are on track to deliver their benefits case
4. `compare_project_health(project_ids=["alpha", "beta", "gamma", "delta", "epsilon"])` — side-by-side health comparison across key dimensions for all five projects

**The output**

Claude returns a portfolio picture structured for committee use:

**Portfolio DCA distribution:** Five projects in the portfolio. One Green (Project Alpha), two Amber-Green (Projects Beta and Delta), one Amber (Project Gamma), one Amber-Red (Project Epsilon). No projects are currently rated Red. The portfolio's overall delivery confidence is Amber-Green — the majority of projects are performing adequately, but one project presents a risk profile that warrants committee attention.

**Gate readiness ranking:** Two projects have gates in the next 90 days. Project Gamma has a Gate 3 in six weeks — readiness score 58%, below the 70% threshold typically associated with confident gate passage. Project Beta has a Gate 2 in 10 weeks — readiness score 74%, on track. Project Epsilon does not have a gate scheduled but has flagged readiness concerns in the current period.

**Benefits confidence by project:** Three projects have all registered benefits on track. Project Gamma has two of seven benefits at risk. Project Epsilon has three of five benefits at risk, with the primary cashable efficiency saving now forecast to deliver at 60% of the approved target — a material reduction in the benefits case. Across the portfolio, 79% of approved benefits are currently on track. The strategic target is 85%. The portfolio is 6 percentage points below target on benefits realisation.

**Cross-project comparison:** The comparison highlights three dimensions where the portfolio shows systemic weakness: Risk Management (three of five projects have stale registers or High risks without mitigation), ARMM maturity (only one project has reached Level 2), and schedule (two projects have AI-forecast completion dates materially beyond their planned dates).

**How to use it**

Structure your committee presentation around three messages. First, the headline: the portfolio is Amber-Green overall, which means most projects are performing but you have two that need specific attention. Second, the specific attention items: Project Gamma's Gate 3 readiness and Project Epsilon's benefits shortfall are the two items that require committee awareness and possibly a decision. Third, the systemic finding: risk management and ARMM maturity are weak across the portfolio, which is a governance quality issue that needs a portfolio-level response rather than individual project fixes.

For Project Epsilon's benefits shortfall, the committee needs to consider whether the remaining benefits case (at 60% of approved value) still justifies the continuing investment. That is a decision for the committee, not for you to pre-empt — but you need to surface it clearly. Prepare a one-page benefits position for Epsilon specifically.

For Project Gamma's Gate 3, tell the committee the gate is six weeks away and readiness is below threshold. If they want a recommendation, the options are: (1) proceed to the gate and accept conditions, (2) defer the gate by four to six weeks to resolve the gaps, or (3) direct additional assurance resource at Gamma immediately. Ask Claude to run the Full Gate Readiness Analysis for Gamma to give the committee a full picture before they decide.

---

### Example 2: Shared resource risk across projects

**Scenario**

You know that three of your five projects are relying on the same technical architect. This has been flagged informally but has not been formally assessed. You need to understand whether this is a real delivery risk, when the conflict peaks, and what options you have to address it.

**What to ask Claude**

> Three of my projects are sharing the same technical architect. Run a proper resource dependency analysis — show me when the conflict peaks, what the portfolio-level risk exposure is, and what options I have.

**What Claude does behind the scenes**

Claude calls four tools:

1. `get_critical_resources()` — identifies key individuals and skills whose commitment affects multiple projects, including the technical architect
2. `detect_resource_conflicts(project_ids=["alpha", "gamma", "epsilon"])` — maps the architect's commitments across the three projects, showing when they are double- or triple-committed
3. `get_portfolio_capacity()` — aggregates resource demand versus supply across the portfolio, contextualising the architect dependency within the broader resource picture
4. `get_portfolio_risks()` — returns the portfolio-level risks, including any existing risk entries for key-person dependencies

**The output**

Claude returns a resource dependency analysis:

**The conflict:** The technical architect is the named resource on critical tasks across all three projects. The peak conflict occurs in weeks 14–20, when she is committed to 140% of available capacity across the three projects simultaneously. Two of the three tasks she is assigned to in that period sit on the critical path of their respective projects.

**Timeline:** The conflict begins in week 11 (minor overlap), peaks in weeks 14–20 (severe overlap, 140% committed), and resolves in week 22 when Project Alpha's integration milestone completes. During weeks 14–20, any absence or focus shift by the architect directly threatens the critical path of two projects.

**Portfolio-level risk exposure:** If the architect is unavailable for a sustained period during weeks 14–20, the cumulative schedule impact across the three projects is estimated at 8–14 weeks of delay. In financial terms, the affected projects have an aggregate EAC of £112m — the delay risk exposure is significant relative to the portfolio's risk reserve.

**Existing risk entry:** There is one risk register entry for key-person dependency (risk R-09 in Project Gamma), rated Medium. It does not reference the cross-project dimension of the dependency and has not been updated in 53 days. The other two projects have no risk entry for this dependency at all.

**How to use it**

You have three practical options, and Claude can help you think through each:

**Option 1 — Stagger timelines.** If any of the three projects has schedule flexibility, defer the tasks requiring the architect's input so they do not overlap with the peak conflict window. Ask Claude: "Which of these three projects has the most schedule flexibility in weeks 14–20 without affecting its gate date?" Claude will run a critical path comparison and identify the candidate.

**Option 2 — Backfill.** Identify a secondary resource who can take on the less critical of the architect's assignments during the conflict window. This requires a skills assessment — ask Claude to check whether a deputy exists in the resource data, or flag that this needs to be escalated to the relevant delivery directors to source.

**Option 3 — Escalate.** If neither option is feasible within existing budgets and timelines, this is a portfolio-level risk that needs an investment committee decision. The aggregate schedule impact of £112m across three projects is material enough to warrant a formal risk escalation.

Regardless of which option you pursue, the risk register entries need updating today. The cross-project dimension of this dependency is not captured anywhere. Ask each project's PM to update their risk registers to reflect it, and ask Claude to draft a portfolio-level risk entry you can register centrally.

---

### Example 3: Prioritising your next assurance review slot

**Scenario**

You have one assurance review slot available next month. Five projects are competing for it. You need to prioritise objectively — which project presents the highest combined delivery risk and most urgently needs external scrutiny?

**What to ask Claude**

> I have one assurance review slot next month. Rank my five projects by composite delivery risk and tell me which needs the review most urgently, and what type of review each needs.

**What Claude does behind the scenes**

Claude calls five tools:

1. `get_portfolio_health()` — current DCA ratings across all five projects, establishing the baseline health picture
2. `get_risk_velocity(project_ids=["alpha", "beta", "gamma", "delta", "epsilon"])` — which projects' risk profiles are deteriorating fastest
3. `detect_stale_risks(project_ids=["alpha", "beta", "gamma", "delta", "epsilon"])` — which projects have governance quality concerns visible in their risk management
4. `get_portfolio_gate_readiness()` — which projects have upcoming gates that an assurance review could meaningfully inform
5. `get_portfolio_armm_summary()` — ARMM maturity across the portfolio, identifying projects where the assurance framework itself is immature

**The output**

Claude returns a ranked prioritisation:

**Rank 1 — Project Epsilon (highest composite risk)**
DCA: Amber-Red. Risk velocity is the highest in the portfolio — three risks have accelerated in the last four weeks. The stale register score is 41%. ARMM maturity is Level 0 — the lowest in the portfolio. No gate is scheduled, which means there is no external forcing mechanism to drive improvement. Benefits shortfall (three of five benefits at risk) makes this the project with the greatest strategic value at stake. Recommended review type: a full Departmental Assurance Review with benefits realisation focus.

**Rank 2 — Project Gamma (gate in six weeks)**
DCA: Amber. Readiness score is 58% against a Gate 3 in six weeks. Risk register has four High risks without active mitigation. The gate creates a natural forcing mechanism, but the low readiness score suggests the programme needs support, not just challenge. Recommended review type: a targeted pre-gate assurance review focusing on the readiness gaps — financial position, ARMM improvement, and risk mitigation.

**Ranks 3–5 — Projects Alpha, Beta, Delta**
All three are Amber-Green or Green. Risk velocity is low. No gates in the next 90 days. Stale register scores are within acceptable range. These projects do not require an active assurance review at this time — monitoring through quarterly health checks is sufficient.

**Recommendation:** Allocate the review slot to Project Epsilon. The combination of Amber-Red DCA, highest risk velocity, lowest ARMM maturity, and material benefits shortfall makes Epsilon the project where independent external scrutiny will have the most impact. Project Gamma's gate in six weeks creates urgency but has a natural assurance mechanism already — the gate review itself. Consider whether a rapid pre-gate support visit to Gamma (lighter touch than a full review) can be arranged alongside the Epsilon review, potentially using a different team member.

**How to use it**

The ranking gives you an evidence-based justification for the allocation decision — important when other delivery directors will inevitably push back on why their project was not selected. The rationale is objective: composite risk score based on five independent indicators.

For Project Epsilon, the Departmental Assurance Review should focus on three things: the benefits case (is it still viable?), the risk management quality (why are so many risks accelerating without mitigation?), and the ARMM maturity (Level 0 means the assurance framework does not exist — this is systemic). Ask the review team to use the Full Gate Readiness Analysis research prompt as their preparation tool.

For Project Gamma, schedule a conversation with the project board chair two weeks before the gate to discuss the readiness position. If the gap between current readiness (58%) and the gate threshold cannot be closed in six weeks, deferral is the responsible course. The platform's gate readiness trend data will tell you whether readiness is improving fast enough to make the gate viable.

---

## Tips for best results

**Use consistent project IDs across all queries.** The platform stores project data against identifiers. Using the same identifier in each session ensures Claude is reading from the correct project records. If you are running portfolio analysis, tell Claude the full list of project IDs at the start of the session.

**Run per-project analysis before portfolio comparison.** The richest portfolio analysis comes from running Research Prompt 1 for each project individually, then asking Claude to compare. The `compare_project_health` tool produces more meaningful output when it has full per-project data to draw on.

**Ask for portfolio framing explicitly.** Claude is set up to lead with portfolio-level analysis when the Portfolio Manager system prompt is active, but if a response drifts into individual project operational detail, redirect it: "I need this at portfolio level — which projects, which patterns, which priorities."

**Use the prioritisation workflow quarterly.** The assurance prioritisation analysis (Example 3) is most valuable as a standing quarterly exercise, not just when you have a specific review slot to fill. Run it at the start of each quarter to get an objective read on where the portfolio risk is accumulating.

**Flag systemic findings to project boards.** When the platform identifies a pattern across multiple projects — stale risk registers, low ARMM maturity, shared assumptions not stress-tested — that finding belongs at the portfolio level, not in individual project board reports. Raise it as a portfolio-wide governance concern and direct each project's SRO to respond.

**Combine portfolio analysis with the investment committee narrative.** The `get_portfolio_brm_overview` output gives you the aggregate benefits confidence figure to compare against your strategic target. If the portfolio is below target on benefits realisation, that is the most important thing to say to an investment committee — it goes directly to whether the investment is delivering the value that was approved.

---

## Related guides and prompts

- `docs/guides/first-project.md` — how to connect Claude to the platform and load a project
- `docs/prompts/role-system-prompts.md` — the Portfolio Manager system prompt and all other role prompts
- `docs/prompts/research-prompts.md` — Full Gate Readiness Analysis (for running across each project before portfolio comparison)
- `docs/guides/sro-guide.md` — the SRO guide, for when you need to understand individual programme accountability
- `docs/guides/assurance-reviewer-guide.md` — the assurance reviewer guide, for when you are directing a review team at one of your portfolio projects
