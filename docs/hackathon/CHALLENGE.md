# The Challenge: From PDF to Board Pack in Under 60 Seconds

## Scenario

You've just been appointed SRO for a major government programme. Your Investment Committee meets tomorrow. You have the business case but no assurance baseline — no domain classification, no maturity assessment, no assumption register, no compliance history, no DCA narrative.

You need all of it. Now.

---

## The Prompt

Paste this into Claude.ai (with the PDA Platform MCP server connected):

```
I've just been appointed SRO for the National Schools Digital Infrastructure
Programme (NSDIP) at the Department for Education. £2.4bn whole life cost,
Digital/ICT category.

Complexity indicators: technical 0.85, stakeholder 0.6, requirement clarity 0.3,
delivery track record 0.2, organisational change 0.8, regulatory 0.5,
dependencies 0.7.

Key risks: legacy system integration, teacher adoption resistance,
data migration from 22,000 schools, ministerial timeline pressure.

I need a full assurance baseline before my Investment Committee tomorrow:
1. Create the project and run the full OPAL pipeline
2. Classify the complexity domain
3. Set up assumption tracking for the £2.4bn cost envelope
4. Run the full assurance workflow
5. Generate a DCA narrative for the quarterly return
6. Export me a dashboard I can email to the board
```

---

## What Happens

Claude reads the prompt and calls 9+ MCP tools in sequence:

| # | Tool | What it does |
|---|------|-------------|
| 1 | `create_project_from_profile` | Creates project + generates 12 months of OPAL data |
| 2 | `classify_project_domain` | Classifies as COMPLEX using 7 indicators |
| 3 | `ingest_assumption` | Registers £2.4bn cost assumption with baseline |
| 4 | `run_assurance_workflow` | Runs FULL_ASSURANCE across OPAL-1 to OPAL-8 |
| 5 | `get_assumption_drift` | Shows assumption health baseline |
| 6 | `nista_longitudinal_trend` | 12-month compliance trend |
| 7 | `review_action_status` | Open review actions from P3 |
| 8 | `generate_narrative` | AI-written DCA narrative (pm-nista) |
| 9 | `export_dashboard_html` | Self-contained HTML dashboard |

The output: a complete assurance baseline with dashboard, ready to email.

---

## The Numbers

- **126** MCP tools available
- **18** modules
- **14** assurance modules (P1–P14)
- **251** ARMM maturity criteria
- **4** Cynefin complexity domains
- **9** Verified Autonomy framework layers, all wired
- **~60 seconds** end to end
- **1** prompt

---

## Research Foundation

Based on: *From Policy to Practice: An Open Framework for AI-Ready Project Delivery* (Newman, 2026)
DOI: https://doi.org/10.5281/zenodo.18711384

---

## Try It Yourself

See [QUICKSTART.md](QUICKSTART.md) for connection instructions.
