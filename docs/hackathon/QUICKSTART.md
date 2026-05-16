# Connect to the PDA Platform

The PDA Platform is a live MCP server with 126 project assurance tools across 18 modules. Connect in under 30 seconds.

**Server URL:** `https://pda-platform-i33p.onrender.com/sse`

---

## Claude.ai (recommended)

1. Go to [claude.ai](https://claude.ai) and sign in
2. Click your name (bottom-left) → **Settings**
3. Click **Integrations** in the left sidebar
4. Click **Add Custom Integration**
5. **Name:** `PDA Platform`
6. **URL:** `https://pda-platform-i33p.onrender.com/sse`
7. Click **Connect**
8. Return to a new chat — the 126 PDA tools will appear in the tools menu

**Note:** The first request may take 30-60 seconds if the server is cold (free tier). Subsequent requests are instant.

---

## Claude Desktop

Add to your config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "python",
      "args": ["-m", "pm_mcp_servers.pm_assure.server"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\pda-platform\\packages\\pm-data-tools\\src;C:\\path\\to\\pda-platform\\packages\\agent-task-planning\\src;C:\\path\\to\\pda-platform\\packages\\pm-mcp-servers\\src"
      }
    }
  }
}
```

Or use the remote SSE server (no local install needed):

```json
{
  "mcpServers": {
    "pda-platform": {
      "url": "https://pda-platform-i33p.onrender.com/sse"
    }
  }
}
```

Restart Claude Desktop after saving.

---

## ChatGPT / Gemini / Other AI Platforms

Any MCP-compatible client can connect using the same server URL:

`https://pda-platform-i33p.onrender.com/sse`

The PDA Platform REST API is also available at:
`https://pda-platform-i33p.onrender.com/docs` (interactive Swagger UI)

---

## What's Available

126 tools across 18 modules. Highlights:

### Project Data (6 tools)
- Load MS Project, Primavera P6, Jira, Monday, Smartsheet, GMPP, and NISTA files
- Query tasks, get critical path, analyse dependencies, export to other formats

### Analysis (6 tools)
- Risk identification, schedule forecasting (Monte Carlo / EVM)
- Outlier detection, health assessment, mitigation suggestions, baseline comparison

### Validation (4 tools)
- Structure, semantic, NISTA compliance, and custom rule validation

### GMPP & NISTA (5 tools)
- GMPP quarterly report generation
- AI narrative generation (DCA, cost, schedule, benefits, risk)
- NISTA API submission (sandbox/production)
- NISTA metadata fetch and report validation

### Assurance (27 tools)
- **P1** Artefact currency checks
- **P2** Longitudinal compliance tracking
- **P3** Review action extraction and tracking
- **P4** AI confidence divergence monitoring
- **P5** Adaptive review scheduling
- **P6** Governance override logging and pattern analysis
- **P7** Lessons learned ingestion and search
- **P8** Assurance overhead tracking and optimisation
- **P9** Agentic workflow orchestration
- **P10** Cynefin domain classification
- **P11** Assumption drift tracking and cascade impact
- **P12** ARMM maturity assessment (251 criteria, 4 dimensions)
- **P14** Gate readiness assessment (GATE_0 through PAR)
- Project creation from profile, dashboard data/HTML export, ARMM reports

### Benefits Realisation Management (10 tools)
- **P13** Benefit registration, measurement tracking, drift detection
- Dependency network mapping, cascade impact analysis
- Realisation forecasting, maturity assessment, portfolio overview

---

## Quick Test

After connecting, paste this into your chat:

```
Create a test project called "Quick Test" for HMRC, domain COMPLICATED,
technical complexity 0.6. Then tell me the compliance score and domain
classification.
```

Claude will call `create_project_from_profile` and report back with the results.

---

## Links

- **GitHub:** [github.com/antnewman/pda-platform](https://github.com/antnewman/pda-platform)
- **UDS Spec:** [github.com/Tortoise-AI/uds](https://github.com/Tortoise-AI/uds)
- **Paper:** [doi.org/10.5281/zenodo.18711384](https://doi.org/10.5281/zenodo.18711384)
- **TortoiseAI:** [tortoiseai.co.uk](https://tortoiseai.co.uk)
