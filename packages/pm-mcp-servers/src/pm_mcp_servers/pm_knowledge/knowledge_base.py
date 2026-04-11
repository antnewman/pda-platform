"""Pre-loaded knowledge base for UK government project delivery assurance."""

from __future__ import annotations

# ── Benchmark data ────────────────────────────────────────────────────────────
# Sources: IPA Annual Reports 2019-2024, NAO reports, GMPP data, academic research

BENCHMARK_DATA: dict[str, dict[str, dict]] = {
    "IT_AND_DIGITAL": {
        "cost_overrun": {
            "mean_percent": 27,
            "median_percent": 15,
            "p80_percent": 55,
            "source": "IPA Annual Report 2023; NAO digital transformation review 2022",
            "note": "Overrun measured from approved Full Business Case baseline. Projects with scope changes excluded from median but included in mean.",
            "sample_size": "142 major IT/digital projects 2015-2023",
        },
        "schedule_slip": {
            "mean_months": 14,
            "median_months": 8,
            "p80_months": 28,
            "percent_late": 68,
            "source": "IPA Annual Report 2023; NAO digital project performance review",
            "note": "Slippage measured from Gate 3 baseline completion date.",
        },
        "dca_distribution": {
            "green": 8,
            "amber_green": 31,
            "amber": 38,
            "amber_red": 17,
            "red": 6,
            "source": "IPA GMPP Annual Report 2023 — IT/Digital project cohort",
            "note": "Percentages. Green projects are rare in this category at Gate 3+.",
        },
        "common_overrun_drivers": [
            "Requirements instability — scope defined too late or changed post-FBC",
            "Legacy system complexity underestimated at business case stage",
            "Optimism bias not applied to software development estimates",
            "Data migration complexity consistently underestimated",
            "Supplier capability not independently assessed before contract award",
            "Agile delivery adopted in name but waterfall governance applied in practice",
        ],
    },
    "INFRASTRUCTURE": {
        "cost_overrun": {
            "mean_percent": 18,
            "median_percent": 12,
            "p80_percent": 38,
            "source": "IPA Annual Report 2023; Flyvbjerg infrastructure megaproject database",
            "note": "UK government civil infrastructure. Excludes defence.",
            "sample_size": "87 major infrastructure projects 2015-2023",
        },
        "schedule_slip": {
            "mean_months": 11,
            "median_months": 6,
            "p80_months": 22,
            "percent_late": 52,
            "source": "IPA Annual Report 2023",
            "note": "Planning consent delays excluded from delivery phase slip calculations.",
        },
        "dca_distribution": {
            "green": 12,
            "amber_green": 38,
            "amber": 33,
            "amber_red": 13,
            "red": 4,
            "source": "IPA GMPP Annual Report 2023 — Infrastructure cohort",
        },
        "common_overrun_drivers": [
            "Ground condition surveys inadequate — subsurface risk materialises during construction",
            "Planning and consenting delays cascade into construction programme",
            "Supply chain capacity constraints — specialist contractors unavailable at agreed rates",
            "Utility diversions more complex and costly than assessed",
            "Scope additions approved outside change control erode contingency",
            "Weather and seasonal constraints underweighted in schedule risk",
        ],
    },
    "DEFENCE": {
        "cost_overrun": {
            "mean_percent": 40,
            "median_percent": 22,
            "p80_percent": 80,
            "source": "NAO Major Projects Report 2023; IPA Annual Report 2023",
            "note": "Defence Equipment Plan programmes. Overrun from MRPV baseline.",
            "sample_size": "32 major defence programmes 2015-2023",
        },
        "schedule_slip": {
            "mean_months": 24,
            "median_months": 16,
            "p80_months": 48,
            "percent_late": 78,
            "source": "NAO Major Projects Report 2023",
            "note": "Includes both procurement and in-service delivery phases.",
        },
        "dca_distribution": {
            "green": 3,
            "amber_green": 19,
            "amber": 41,
            "amber_red": 28,
            "red": 9,
            "source": "IPA GMPP Annual Report 2023 — Defence cohort",
            "note": "Defence programmes consistently carry the highest proportion of Amber/Red and Red ratings in GMPP.",
        },
        "common_overrun_drivers": [
            "Technology readiness level overestimated at business case — development risk materialises post-contract",
            "Single-source procurement with insufficient commercial leverage",
            "Requirement changes driven by operational theatre developments",
            "Export licence and international partner dependencies",
            "Long programme durations mean original assumptions are rarely still valid at delivery",
            "Concurrency — production begun before development complete",
        ],
    },
    "HEALTH_AND_SOCIAL_CARE": {
        "cost_overrun": {
            "mean_percent": 22,
            "median_percent": 14,
            "p80_percent": 45,
            "source": "IPA Annual Report 2023; NAO health IT review",
            "sample_size": "41 major health transformation programmes 2015-2023",
        },
        "schedule_slip": {
            "mean_months": 18,
            "median_months": 10,
            "p80_months": 36,
            "percent_late": 71,
            "source": "IPA Annual Report 2023",
            "note": "NHS digital transformation programmes dominate this cohort.",
        },
        "common_overrun_drivers": [
            "Clinical engagement required but not secured before delivery begins",
            "NHS interoperability and data standards more complex than anticipated",
            "TUPE and workforce transfer complications",
            "Regulatory and CQC compliance requirements evolve during delivery",
            "Benefits dependent on behaviour change by clinical staff — hardest to deliver",
        ],
    },
    "CROSS_GOVERNMENT": {
        "cost_overrun": {
            "mean_percent": 25,
            "median_percent": 13,
            "p80_percent": 50,
            "source": "IPA GMPP Annual Report 2023 — all projects",
            "note": "Whole-portfolio average across all GMPP project types.",
            "sample_size": "235 live GMPP projects at time of report",
        },
        "schedule_slip": {
            "mean_months": 14,
            "median_months": 8,
            "p80_months": 27,
            "percent_late": 60,
            "source": "IPA GMPP Annual Report 2023",
        },
        "dca_distribution": {
            "green": 9,
            "amber_green": 33,
            "amber": 36,
            "amber_red": 16,
            "red": 6,
            "source": "IPA GMPP Annual Report 2023 — all cohorts combined",
            "note": "Only 9% of GMPP projects are rated Green. Amber is the modal rating.",
        },
        "optimism_bias_reference": {
            "it_and_digital_works": {"lower": 10, "upper": 200},
            "standard_civil_engineering": {"lower": 3, "upper": 44},
            "non_standard_civil_engineering": {"lower": 6, "upper": 66},
            "equipment_development": {"lower": 10, "upper": 200},
            "source": "HM Treasury Green Book Supplementary Guidance: Optimism Bias (2022)",
            "note": "Upper bound optimism bias adjustment percentages for cost estimates at business case stage, before risk adjustment.",
        },
    },
}

# ── Failure patterns ──────────────────────────────────────────────────────────

FAILURE_PATTERNS: list[dict] = [
    {
        "id": "FP001",
        "name": "Optimism Bias Not Corrected",
        "domains": ["ALL"],
        "gates": ["GATE_1", "GATE_2", "GATE_3"],
        "frequency": "Very Common",
        "impact": "High",
        "description": (
            "Cost and schedule estimates at business case are systematically optimistic. "
            "Green Book requires optimism bias to be applied to raw estimates before risk adjustment. "
            "Projects that skip this step typically underestimate cost by 15-40% and schedule by 20-50%."
        ),
        "indicators": [
            "Business case cost estimate has no optimism bias adjustment documented",
            "Estimate based solely on analogous projects without a formal reference class forecast",
            "Schedule assumes no rework, no procurement delays, and continuous resourcing",
            "P50 cost used for budget setting rather than P80",
        ],
        "ipa_reference": "IPA Annual Report 2023; HM Treasury Green Book Optimism Bias Guidance",
        "mitigation": (
            "Apply HM Treasury optimism bias uplift percentages to raw estimates. "
            "Conduct reference class forecasting using comparable completed projects. "
            "Set budget at P80, not P50."
        ),
    },
    {
        "id": "FP002",
        "name": "SRO Capacity and Authority Insufficient",
        "domains": ["ALL"],
        "gates": ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4"],
        "frequency": "Common",
        "impact": "Very High",
        "description": (
            "The Senior Responsible Owner lacks the time, seniority, or authority to drive delivery. "
            "IPA research consistently identifies SRO effectiveness as a primary determinant of programme success. "
            "SROs typically need to dedicate 30-50% of their time to a major programme."
        ),
        "indicators": [
            "SRO also holds multiple other major programme accountabilities simultaneously",
            "SRO is below SCS2 grade for a programme of significant scale",
            "SRO changes more than once in a 12-month period",
            "Board minutes show SRO absent from key governance decisions",
            "SRO unable to resolve issues that have been escalated — decisions are deferred repeatedly",
        ],
        "ipa_reference": "IPA Project Leadership guidance; IPA Annual Report 2022",
        "mitigation": (
            "Confirm SRO time commitment at each gate. "
            "Appoint a Deputy SRO for operational matters if SRO capacity is constrained. "
            "Ensure SRO has direct line to minister or board for escalation without obstruction."
        ),
    },
    {
        "id": "FP003",
        "name": "Requirements Defined Too Late",
        "domains": ["IT_AND_DIGITAL", "HEALTH_AND_SOCIAL_CARE"],
        "gates": ["GATE_2", "GATE_3"],
        "frequency": "Very Common",
        "impact": "High",
        "description": (
            "User and business requirements are not sufficiently defined before procurement or development begins. "
            "This is the single most common driver of scope change, cost overrun, and schedule slip in IT projects. "
            "NAO research links late requirements definition to an average 34% cost premium."
        ),
        "indicators": [
            "Requirements document is high-level at Gate 2 with 'TBC' sections",
            "User research not completed before OBC approval",
            "Procurement documents reference requirements 'to be agreed during contract'",
            "Agile delivery adopted without a minimum viable product definition agreed upfront",
            "Multiple stakeholder groups each claiming ownership of requirements with no resolution",
        ],
        "ipa_reference": "NAO digital transformation review 2022; GDS Service Standard",
        "mitigation": (
            "Complete discovery and alpha phases before OBC approval for IT projects. "
            "Require a signed-off requirements baseline as a condition of Gate 3. "
            "Use a Product Owner with authority to arbitrate requirements disputes."
        ),
    },
    {
        "id": "FP004",
        "name": "Benefits Ownership Not Established",
        "domains": ["ALL"],
        "gates": ["GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5"],
        "frequency": "Very Common",
        "impact": "High",
        "description": (
            "Benefits are not assigned to named owners who are accountable for their realisation. "
            "Without ownership, benefits drift unmeasured until post-project review reveals they were not delivered. "
            "IPA finds that 40%+ of projects cannot demonstrate benefits realisation at Gate 5."
        ),
        "indicators": [
            "Benefits register lists benefits without named benefit owners",
            "Benefit owners are in different organisations from the project and have not confirmed accountability",
            "Benefits are defined in terms of outputs (deliverables) not outcomes (measurable change)",
            "No baseline measurement established — benefits cannot be proved or disproved",
            "Benefits realisation plan is not kept current beyond Gate 3",
        ],
        "ipa_reference": "IPA Benefits Management Guidance; HM Treasury Green Book 2022",
        "mitigation": (
            "Require named benefit owners to sign off the benefits register at each gate. "
            "Define benefits in SMART terms with a baseline and a measurement method. "
            "Ensure benefit owners are in the governance structure and receive regular reporting."
        ),
    },
    {
        "id": "FP005",
        "name": "Risk Register Not Actively Managed",
        "domains": ["ALL"],
        "gates": ["GATE_2", "GATE_3", "GATE_4"],
        "frequency": "Common",
        "impact": "High",
        "description": (
            "The risk register exists but is not actively maintained. Risks are not updated, owners are not engaged, "
            "and mitigations are not resourced. A static risk register provides a false sense of assurance and "
            "means issues materialise without warning."
        ),
        "indicators": [
            "Risk register last updated more than 4 weeks ago",
            "Risks rated High or Very High with no mitigation actions logged",
            "The same risks appear unchanged across multiple reporting periods",
            "Risk owners are listed but have not formally accepted ownership",
            "No risk tolerance or appetite statement against which risks are assessed",
            "Issues register separate from risk register — no pathway from risk to issue",
        ],
        "ipa_reference": "IPA Risk Management guidance; M_o_R framework",
        "mitigation": (
            "Require monthly risk register updates as a governance condition. "
            "Risk owners to report to project board, not just to the PM. "
            "Set formal risk tolerance levels and escalate automatically when breached."
        ),
    },
    {
        "id": "FP006",
        "name": "Schedule Float Consumed Early",
        "domains": ["ALL"],
        "gates": ["GATE_3", "GATE_4"],
        "frequency": "Common",
        "impact": "High",
        "description": (
            "Float on the critical path and near-critical paths is consumed in the early stages of delivery, "
            "leaving no buffer for the inevitable issues that arise later. This pattern typically manifests as "
            "a Green or Amber/Green project that suddenly deteriorates to Amber/Red in the final third of delivery."
        ),
        "indicators": [
            "Float on the longest path has reduced by more than 30% since baseline",
            "Near-critical paths (float within 2 weeks of critical path) exist and are not being monitored",
            "Programme-level schedule contingency has been partially consumed before Gate 4",
            "Schedule shows tasks completing late being recovered by 'crashing' later tasks",
            "Milestone trend chart shows consistent rightward drift",
        ],
        "ipa_reference": "IPA Schedule Management guidance; AACE Schedule Quality",
        "mitigation": (
            "Track float consumption at project board level, not just task level. "
            "Trigger an escalation process when float falls below a defined threshold. "
            "Reserve programme-level schedule contingency for use by SRO/board, not PM."
        ),
    },
    {
        "id": "FP007",
        "name": "Single Supplier Dependency",
        "domains": ["IT_AND_DIGITAL", "DEFENCE", "INFRASTRUCTURE"],
        "gates": ["GATE_2", "GATE_3"],
        "frequency": "Moderate",
        "impact": "Very High",
        "description": (
            "A single supplier holds a disproportionate share of delivery risk with limited ability for the "
            "client to switch or exert competitive pressure. This is particularly acute in IT where the supplier "
            "holds data, IP, or system knowledge that creates lock-in."
        ),
        "indicators": [
            "One supplier accounts for more than 60% of contract value",
            "Exit provisions in the contract are impractical to invoke without service failure",
            "Supplier holds all technical IP with no client-side access",
            "No viable alternative suppliers have been assessed",
            "Supplier financial health has not been reviewed since contract award",
        ],
        "ipa_reference": "Cabinet Office commercial playbook; Crown Commercial Service guidance",
        "mitigation": (
            "Require annual financial health checks on critical suppliers. "
            "Ensure IP and data ownership is clearly contracted on client side. "
            "Build exit provisions that are genuinely executable — test them at contract award."
        ),
    },
    {
        "id": "FP008",
        "name": "Governance Too Complex",
        "domains": ["ALL"],
        "gates": ["GATE_1", "GATE_2", "GATE_3"],
        "frequency": "Moderate",
        "impact": "Medium",
        "description": (
            "Decision-making is distributed across too many boards, committees, and approval bodies, "
            "creating delays, confusion about accountability, and a tendency for issues to circulate "
            "without resolution. This is particularly common in cross-departmental and joint programmes."
        ),
        "indicators": [
            "More than four governance tiers between delivery team and SRO",
            "The same decision requires approval from more than three bodies",
            "Board terms of reference overlap — multiple boards claim authority for the same decisions",
            "Issues have been 'noted' repeatedly in board minutes without a decision",
            "Programme team spends more than 20% of time on governance overhead",
        ],
        "ipa_reference": "IPA Governance guidance; Cabinet Office portfolio management framework",
        "mitigation": (
            "Map decisions to a single accountable body. "
            "Reduce governance tiers to maximum three (delivery, programme, sponsorship). "
            "Introduce a RAG-triggered escalation protocol so issues move to the right level automatically."
        ),
    },
]

# ── IPA and HMT guidance references ──────────────────────────────────────────

GUIDANCE_REFERENCES: list[dict] = [
    {
        "id": "G001",
        "topic": "optimism_bias",
        "title": "Supplementary Green Book Guidance: Optimism Bias",
        "publisher": "HM Treasury",
        "year": 2022,
        "summary": (
            "Optimism bias is the demonstrated systematic tendency for project appraisers to be "
            "over-optimistic about key parameters. HM Treasury requires optimism bias uplifts to be "
            "applied to raw cost and time estimates at business case stage before risk adjustment. "
            "Uplifts range from 3% (standard civil engineering, lower bound) to 200% "
            "(IT/equipment development, upper bound). Projects should justify any departure from "
            "the reference class uplift with specific evidence."
        ),
        "key_thresholds": {
            "it_upper_bound": "200% cost uplift",
            "it_lower_bound": "10% cost uplift",
            "civil_engineering_upper": "44% cost uplift",
            "civil_engineering_lower": "3% cost uplift",
        },
        "url": "https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias",
    },
    {
        "id": "G002",
        "topic": "green_book",
        "title": "The Green Book: Central Government Guidance on Appraisal and Evaluation",
        "publisher": "HM Treasury",
        "year": 2022,
        "summary": (
            "The Green Book sets out HM Treasury guidance for appraisal and evaluation of all policies, "
            "programmes, and projects. It requires a five-case business case model (strategic, economic, "
            "commercial, financial, management). Benefits must be monetised where possible using "
            "standard HM Treasury values. The Social Time Preference Rate (3.5%) is used for discounting. "
            "All major projects (over £5m) require a business case compliant with Green Book principles."
        ),
        "key_thresholds": {
            "mandatory_business_case_threshold": "£5m project value",
            "hmt_approval_threshold": "£100m or novel/contentious",
            "discount_rate": "3.5% real (social time preference rate)",
            "vfm_assessment": "Required for all options in the economic case",
        },
        "url": "https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government",
    },
    {
        "id": "G003",
        "topic": "cabinet_office_controls",
        "title": "Cabinet Office Spending Controls",
        "publisher": "Cabinet Office / HM Treasury",
        "year": 2023,
        "summary": (
            "Cabinet Office controls require departments to seek approval for certain categories of spend. "
            "ICT spend above £5m requires Cabinet Office digital spend approval. "
            "Consultancy and contingent labour above £600k requires approval. "
            "Property above £1m requires approval. "
            "All major projects (WLC above £30m) must be registered on GMPP. "
            "Novel, contentious, or repercussive proposals require additional HMT clearance."
        ),
        "key_thresholds": {
            "ict_approval_threshold": "£5m",
            "consultancy_approval_threshold": "£600k",
            "property_approval_threshold": "£1m",
            "gmpp_registration_threshold": "£30m whole-life cost",
            "major_project_threshold": "£30m whole-life cost or novel/contentious",
        },
        "url": "https://www.gov.uk/government/publications/cabinet-office-controls",
    },
    {
        "id": "G004",
        "topic": "ipa_annual_report",
        "title": "IPA Annual Report on Major Projects 2022-23",
        "publisher": "Infrastructure and Projects Authority",
        "year": 2023,
        "summary": (
            "The IPA Annual Report provides an assessment of the Government Major Projects Portfolio (GMPP). "
            "In 2022-23, 235 projects were in the GMPP with a whole-life cost of approximately £791bn. "
            "9% were rated Green, 33% Amber/Green, 36% Amber, 16% Amber/Red, 6% Red. "
            "The report identifies digital and technology projects as the highest-risk category. "
            "Key themes: the need for stronger benefits management, earlier supplier engagement, "
            "and more realistic schedule planning."
        ),
        "key_statistics": {
            "gmpp_project_count": 235,
            "gmpp_whole_life_cost_bn": 791,
            "green_percent": 9,
            "amber_green_percent": 33,
            "amber_percent": 36,
            "amber_red_percent": 16,
            "red_percent": 6,
        },
        "url": "https://www.gov.uk/government/publications/infrastructure-and-projects-authority-annual-report-2022-to-2023",
    },
    {
        "id": "G005",
        "topic": "gmpp_reporting",
        "title": "GMPP Reporting Requirements and RAG Rating Definitions",
        "publisher": "Infrastructure and Projects Authority",
        "year": 2023,
        "summary": (
            "GMPP projects must submit quarterly data returns including the Integrated Assurance and "
            "Approval Plan (IAAP), highlight reports, and updated risk registers. "
            "DCA ratings are set by the IPA independently of departmental self-assessment. "
            "RAG ratings cover: Time, Cost, Benefits, and Delivery Confidence. "
            "Projects may self-assess but IPA reserves the right to override where evidence does not "
            "support the claimed rating. Rating changes require IPA countersignature."
        ),
        "key_thresholds": {
            "quarterly_return_frequency": "Quarterly",
            "gate_review_frequency": "At each IPA gate (Gates 0-5 plus PAR)",
            "par_threshold": "All GMPP projects receive a Project Assessment Review annually",
        },
        "url": "https://www.gov.uk/government/publications/project-delivery-functional-standard",
    },
    {
        "id": "G006",
        "topic": "benefits_management",
        "title": "IPA Benefits Management Guidance",
        "publisher": "Infrastructure and Projects Authority",
        "year": 2022,
        "summary": (
            "IPA guidance on benefits management aligned to the Green Book five-case model. "
            "Benefits must be: identified and categorised (financial/non-financial, direct/indirect); "
            "baselined with a pre-intervention measurement; assigned to a named benefit owner; "
            "tracked against a benefits realisation plan; and evaluated at Gate 5 and in post-project review. "
            "The guidance distinguishes outputs (what is delivered), outcomes (what changes), "
            "and impacts (the broader effect on strategic objectives)."
        ),
        "key_principles": [
            "Benefits must be measurable — vague outcomes do not satisfy Green Book requirements",
            "Every benefit requires a named owner outside the project team",
            "Baseline measurement must precede intervention — retrospective baselines are not acceptable",
            "Benefits realisation plans must extend beyond project closure",
            "Post-project evaluation is mandatory for projects above £5m",
        ],
        "url": "https://www.gov.uk/government/publications/benefits-management-and-realisation",
    },
    {
        "id": "G007",
        "topic": "schedule_management",
        "title": "IPA Schedule Management Guidance",
        "publisher": "Infrastructure and Projects Authority",
        "year": 2021,
        "summary": (
            "IPA guidance on schedule management for major projects. "
            "Schedules must be resource-loaded, logic-linked, and baselined at Gate 3. "
            "The critical path must be actively managed and float monitored. "
            "Schedule contingency (management reserve) should be held at programme level, "
            "not distributed into individual task estimates. "
            "Milestone trend analysis is recommended for tracking schedule health over time. "
            "P80 completion dates should be used for external commitment, not P50."
        ),
        "key_principles": [
            "Resource-loaded schedule required from Gate 2",
            "Logic links (FS, SS, FF) required — no bare starts",
            "Critical path formally identified and owner assigned",
            "Total float on critical path must be zero — negative float indicates delay",
            "Schedule contingency held at SRO/board level, not embedded in tasks",
            "P80 used for ministerial and public commitments",
        ],
        "url": "https://www.gov.uk/government/publications/project-delivery-functional-standard",
    },
    {
        "id": "G008",
        "topic": "project_delivery_functional_standard",
        "title": "Government Functional Standard GovS 002: Project Delivery",
        "publisher": "Cabinet Office",
        "year": 2021,
        "summary": (
            "The mandatory functional standard for project delivery across government. "
            "Sets minimum requirements for how projects and programmes must be governed, managed, "
            "and assured. Requires: a named SRO; a project board with independent members; "
            "a documented business case; a risk register; a benefits realisation plan; "
            "and compliance with IPA assurance requirements. "
            "All civil servants working on major projects must meet the Project Delivery Profession capability framework."
        ),
        "key_requirements": [
            "Named SRO mandatory for all projects above agreed thresholds",
            "Independent project board members required for GMPP projects",
            "Business case must follow Five Case Model",
            "IPA assurance gates mandatory for GMPP projects",
            "Project closure report and lessons learned mandatory",
        ],
        "url": "https://www.gov.uk/government/publications/project-delivery-functional-standard",
    },
]

# ── Knowledge categories ──────────────────────────────────────────────────────

KNOWLEDGE_CATEGORIES = {
    "benchmark_data": {
        "description": "Statistical benchmarks for cost overrun, schedule slip, and DCA distributions by project type",
        "project_types": list(BENCHMARK_DATA.keys()),
        "metrics": ["cost_overrun", "schedule_slip", "dca_distribution", "common_overrun_drivers", "optimism_bias_reference"],
    },
    "failure_patterns": {
        "description": "Common failure modes identified by IPA and NAO research, with indicators and mitigations",
        "count": len(FAILURE_PATTERNS),
        "domains": ["ALL", "IT_AND_DIGITAL", "DEFENCE", "INFRASTRUCTURE", "HEALTH_AND_SOCIAL_CARE"],
        "gates": ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5"],
    },
    "ipa_guidance": {
        "description": "IPA, HM Treasury, and Cabinet Office guidance references with key thresholds and principles",
        "count": len(GUIDANCE_REFERENCES),
        "topics": [g["topic"] for g in GUIDANCE_REFERENCES],
    },
}

# ── Pre-mortem question library ───────────────────────────────────────────────
# Structured challenge questions for IPA gate reviews, keyed by gate and risk flag.
# Based on cognitive science research into optimism bias, planning fallacy,
# escalation of commitment, and groupthink in project governance.

PREMORTEM_QUESTIONS: dict[str, list[dict]] = {
    "GATE_0": [
        {
            "question": "What would have to be true about the strategic context for this programme not to be needed?",
            "targets": ["strategic_rationale"],
            "failure_mode": "Strategic misalignment",
        },
        {
            "question": "Is this programme being driven by evidence of genuine need, or by political momentum that has already made the decision?",
            "targets": ["strategic_rationale", "governance"],
            "failure_mode": "Post-hoc rationalisation",
        },
        {
            "question": "Who has the strongest incentive to see this programme approved, and how might that have shaped the options appraisal?",
            "targets": ["governance", "benefits"],
            "failure_mode": "Optimism bias in options appraisal",
        },
        {
            "question": "If a comparable programme had failed in the last five years, what would have caused that failure — and are those conditions present here?",
            "targets": ["risk", "delivery"],
            "failure_mode": "Failure to learn from reference class",
        },
        {
            "question": "What is the minimum viable version of this programme that would still deliver the core strategic benefit?",
            "targets": ["scope", "benefits"],
            "failure_mode": "Scope overreach",
        },
    ],
    "GATE_1": [
        {
            "question": "What is the reference class for programmes of this type and scale — what does the P80 whole-life cost imply for this estimate?",
            "targets": ["financials", "optimism_bias"],
            "failure_mode": "Optimism bias in cost estimation",
        },
        {
            "question": "Which assumption, if wrong, would most severely undermine the preferred option's value for money?",
            "targets": ["assumptions", "benefits"],
            "failure_mode": "Fragile business case",
        },
        {
            "question": "If the primary benefit fails to materialise, what is the fallback position — and has it been formally assessed?",
            "targets": ["benefits", "risk"],
            "failure_mode": "No contingency in benefits case",
        },
        {
            "question": "Has optimism bias been applied to the schedule as well as to the cost — and has the programme team agreed with the uplift?",
            "targets": ["schedule", "optimism_bias"],
            "failure_mode": "Schedule optimism bias",
        },
        {
            "question": "Are the benefits measurable against a pre-intervention baseline that has already been established?",
            "targets": ["benefits", "measurement"],
            "failure_mode": "Unverifiable benefits",
        },
        {
            "question": "Is the SRO empowered to make the decisions this programme will require — including decisions to descope or stop?",
            "targets": ["governance", "leadership"],
            "failure_mode": "SRO without authority",
        },
    ],
    "GATE_2": [
        {
            "question": "Has the market been genuinely tested, or has a preferred supplier already been identified informally before the procurement begins?",
            "targets": ["commercial", "competition"],
            "failure_mode": "Foregone conclusion procurement",
        },
        {
            "question": "What is the exit strategy if the chosen delivery partner underperforms or fails — and is it genuinely executable?",
            "targets": ["commercial", "risk"],
            "failure_mode": "Supplier lock-in",
        },
        {
            "question": "Is the risk allocation in the proposed contract appropriate — or is the public sector retaining risks that the supplier is better placed to manage?",
            "targets": ["commercial", "risk"],
            "failure_mode": "Poor risk transfer",
        },
        {
            "question": "Has optimism bias been applied to the procurement timeline, not just to the delivery cost?",
            "targets": ["schedule", "commercial"],
            "failure_mode": "Procurement schedule optimism",
        },
        {
            "question": "Are the requirements sufficiently defined to write enforceable contract terms — or will ambiguity create disputes during delivery?",
            "targets": ["requirements", "commercial"],
            "failure_mode": "Ambiguous requirements in contract",
        },
        {
            "question": "What assumptions about supplier capability have been made — and have they been independently verified?",
            "targets": ["commercial", "risk"],
            "failure_mode": "Unverified supplier capability",
        },
    ],
    "GATE_3": [
        {
            "question": "Is the Full Business Case materially different from the Outline Business Case in ways that should have triggered re-approval at a higher level?",
            "targets": ["governance", "financials"],
            "failure_mode": "Scope/cost change without escalation",
        },
        {
            "question": "What will cause the first major milestone to slip — and is there explicit contingency for that scenario?",
            "targets": ["schedule", "risk"],
            "failure_mode": "No schedule contingency for first critical milestone",
        },
        {
            "question": "Are the contract terms genuinely enforceable, or have concessions been made during negotiations that reduce commercial leverage?",
            "targets": ["commercial"],
            "failure_mode": "Negotiation concessions weakening the contract",
        },
        {
            "question": "Has the programme team genuinely tested the schedule by resource-loading it — or does it assume continuous availability of people who have other commitments?",
            "targets": ["schedule", "resources"],
            "failure_mode": "Unresourced schedule",
        },
        {
            "question": "Is there a clear process for managing scope change — and is it understood by the supplier as well as the programme team?",
            "targets": ["scope", "commercial"],
            "failure_mode": "No effective change control",
        },
        {
            "question": "Have all key dependencies on other programmes or external parties been formally agreed and documented?",
            "targets": ["dependencies", "risk"],
            "failure_mode": "Unconfirmed critical dependencies",
        },
        {
            "question": "If this programme had to be stopped six months from now, what would have been wasted — and is that an acceptable risk given current confidence?",
            "targets": ["governance", "risk"],
            "failure_mode": "Sunk cost escalation risk",
        },
    ],
    "GATE_4": [
        {
            "question": "Has user acceptance testing revealed issues that are being accepted as known issues without formal risk acceptance — and who has accepted that risk?",
            "targets": ["quality", "governance"],
            "failure_mode": "Known issues accepted without formal governance",
        },
        {
            "question": "Is the business genuinely ready to absorb this change — or is readiness being claimed under delivery pressure?",
            "targets": ["business_readiness", "change_management"],
            "failure_mode": "Premature go-live under schedule pressure",
        },
        {
            "question": "What will happen to benefits realisation if the hypercare period ends before all go-live issues are resolved?",
            "targets": ["benefits", "risk"],
            "failure_mode": "Benefits undermined by unresolved go-live issues",
        },
        {
            "question": "Are the people who will operate this service trained and confident — or are they being trained on documentation that does not reflect the final system?",
            "targets": ["people", "change_management"],
            "failure_mode": "Inadequate operational readiness",
        },
        {
            "question": "Has the transition plan been tested — including the fallback/rollback scenario if go-live fails?",
            "targets": ["risk", "delivery"],
            "failure_mode": "No tested rollback plan",
        },
    ],
    "GATE_5": [
        {
            "question": "Are the benefits being measured in a way that genuinely attributes outcomes to this programme — or could the same results have occurred without it?",
            "targets": ["benefits", "measurement"],
            "failure_mode": "Attribution failure",
        },
        {
            "question": "What proportion of the intended beneficiaries are experiencing the claimed benefits — and has this been directly measured?",
            "targets": ["benefits", "measurement"],
            "failure_mode": "Benefits claimed but not measured at user level",
        },
        {
            "question": "Have the lessons from this programme been shared in a way that will actually change practice — or just documented in a report nobody will read?",
            "targets": ["lessons_learned", "governance"],
            "failure_mode": "Lessons learned captured but not applied",
        },
        {
            "question": "Is there a credible plan for continuing to track benefits beyond the point at which the programme team disbands?",
            "targets": ["benefits", "governance"],
            "failure_mode": "Benefits orphaned at programme closure",
        },
        {
            "question": "Were the costs ultimately incurred consistent with the approved business case — and if not, has the variance been formally explained?",
            "targets": ["financials", "governance"],
            "failure_mode": "Unexplained final cost variance",
        },
    ],
    "ANY": [
        {
            "question": "If this programme failed to deliver its primary benefit, what is the single most likely cause based on current evidence?",
            "targets": ["benefits", "risk"],
            "failure_mode": "Primary benefit non-delivery",
        },
        {
            "question": "What is the programme team not telling senior stakeholders — and why?",
            "targets": ["governance", "reporting"],
            "failure_mode": "Bad news suppression",
        },
        {
            "question": "Which assumption, if wrong, would most severely undermine the current delivery confidence rating?",
            "targets": ["assumptions", "risk"],
            "failure_mode": "Key assumption failure",
        },
        {
            "question": "Is the risk register a genuine picture of what could go wrong — or a curated list of manageable risks?",
            "targets": ["risk"],
            "failure_mode": "Risk register as compliance exercise",
        },
        {
            "question": "What would a sceptical but fair external reviewer say is the programme's biggest blind spot?",
            "targets": ["governance", "risk"],
            "failure_mode": "Governance blind spot",
        },
    ],
}

# Risk flag to question mapping for targeted pre-mortems
RISK_FLAG_QUESTIONS: dict[str, list[str]] = {
    "optimism_bias": [
        "Has the submitted cost estimate been compared against the IPA benchmark distribution for projects of this type? If so, at what percentile does it sit?",
        "Was optimism bias applied in accordance with HM Treasury Green Book guidance — and was the uplift percentage justified with reference class evidence?",
    ],
    "benefits_unowned": [
        "Who is personally accountable for each benefit — and have those individuals formally accepted accountability in writing?",
        "If a benefit is not realised, who faces consequences — and is that person currently engaged with the programme?",
    ],
    "schedule_no_float": [
        "The schedule shows no float on the critical path. What is the contingency plan if the first critical milestone slips by two weeks?",
        "Has the schedule been independently reviewed for logic quality — are all tasks linked, resource-loaded, and free of artificial constraints?",
    ],
    "supplier_dependency": [
        "What would happen to this programme if the lead supplier became financially distressed or was acquired in the next 12 months?",
        "Is the exit provision in the contract genuinely executable — has it been tested or reviewed by commercial and legal teams?",
    ],
    "stale_risks": [
        "The risk register has not been updated recently. Which risks have been most active in the past 60 days — and why are they not reflected in the register?",
        "Are risk owners actively managing their risks, or has ownership become nominal?",
    ],
    "sro_capacity": [
        "How many days per month is the SRO able to devote to this programme — and is that sufficient given the current delivery stage?",
        "If the SRO were unavailable for four weeks, who would make the decisions that only the SRO can make?",
    ],
}
