# Connecting to PDA Platform

This guide explains how to connect PDA Platform to Claude, ChatGPT, Gemini, or any MCP-compatible client. PDA Platform exposes 126 AI tools across 18 modules for project delivery — data loading, risk analysis, compliance validation, GMPP reporting, calibration evaluation, four-tier escalation routing, and a full assurance framework. Implements the nine-layer Verified Autonomy framework (see [`verified-autonomy-overview.md`](verified-autonomy-overview.md)).

There are two connection methods:

- **Local (stdio)** — install the package on your machine and point your AI client at it. Fast, private, works offline.
- **Remote (SSE)** — connect to a hosted instance over the internet. No installation required.

---

## Option 1: Claude Desktop (Local)

Claude Desktop has native MCP support. This is the fastest way to get started.

### Step 1: Install

```bash
pip install pm-mcp-servers
```

If you need GMPP narrative generation (requires an Anthropic API key):

```bash
pip install "agent-task-planning[anthropic]"
```

### Step 2: Configure

Open your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the PDA Platform server:

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "pda-platform-server",
      "args": [],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Restart the application. You should see PDA Platform listed in the MCP tools panel with 126 tools available.

### Step 4: Test

Try asking Claude:

> "What tools do you have available from PDA Platform?"

---

## Option 2: Claude.ai (Remote)

Claude.ai supports remote MCP servers over SSE. You can connect to a hosted PDA Platform instance without installing anything.

### Using the public instance

1. In Claude.ai, open a conversation
2. Click the **Integrations** icon (plug icon, bottom of the message box)
3. Add a custom MCP server with the URL:

```
https://pda-platform-i33p.onrender.com/sse
```

4. The 126 tools will appear in the conversation

### Hosting your own instance

Click the button below to deploy your own PDA Platform server on Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/antnewman/pda-platform)

Or deploy manually:

```bash
git clone https://github.com/antnewman/pda-platform.git
cd pda-platform
pip install -e packages/pm-data-tools
pip install -e "packages/agent-task-planning[mining,anthropic]"
pip install -e packages/pm-mcp-servers
PORT=8080 pda-platform-remote
```

The server will start at `http://localhost:8080` with endpoints:
- `/sse` — SSE connection for MCP clients
- `/messages` — message endpoint for tool calls
- `/health` — health check

---

## Option 3: Claude Code (Local)

Claude Code supports MCP servers natively.

### Step 1: Install

```bash
pip install pm-mcp-servers
```

### Step 2: Add to your project

In your project's `.claude/settings.json` or your global Claude Code config, add:

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "pda-platform-server",
      "args": [],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Step 3: Use

The 126 tools are now available in your Claude Code session.

---

## Option 4: ChatGPT Desktop

ChatGPT Desktop added MCP support in 2025. Configuration is similar to Claude Desktop.

### Step 1: Install

```bash
pip install pm-mcp-servers
```

### Step 2: Configure

Open ChatGPT Desktop settings and navigate to the MCP servers section. Add a new server:

- **Name:** PDA Platform
- **Command:** `pda-platform-server`
- **Arguments:** (none)

If ChatGPT Desktop requires a config file, the format is:

```json
{
  "mcpServers": {
    "pda-platform": {
      "command": "pda-platform-server",
      "args": []
    }
  }
}
```

### Step 3: Restart and test

Restart ChatGPT Desktop. The PDA Platform tools should appear in the tools panel.

---

## Option 5: Gemini

Google has announced MCP support for Gemini. When available, connect using either:

- **Local:** Point Gemini at `pda-platform-server` (same as Claude/ChatGPT)
- **Remote:** Point Gemini at your SSE endpoint: `https://your-instance.onrender.com/sse`

---

## Option 6: Any MCP Client

PDA Platform works with any MCP-compatible client.

**For local (stdio) clients:**

```bash
pda-platform-server
```

**For remote (SSE) clients:**

```bash
PORT=8080 pda-platform-remote
```

Connect your client to `http://localhost:8080/sse`.

---

## What you get

Once connected, your AI assistant has access to 126 tools across 18 modules:

| Area | Tools | What it does |
|------|-------|-------------|
| **Data** | 6 | Load project files (MS Project, P6, Jira, Monday, Asana, Smartsheet, GMPP, NISTA), query tasks, get critical path, analyse dependencies |
| **Analysis** | 6 | Identify risks, forecast completion (Monte Carlo, EVM), detect outliers, assess health, suggest mitigations, compare baselines |
| **Validation** | 4 | Validate structure, business rules, NISTA compliance, custom rules |
| **NISTA** | 5 | Generate GMPP quarterly reports, AI narratives, submit to NISTA API, fetch metadata, validate reports |
| **Assurance** | 27 | Track assumptions and drift, check artefact currency, analyse review findings, monitor confidence, schedule reviews, log overrides, search lessons learned, measure overhead, run workflows, classify programme complexity, assess gate readiness (P14), generate dashboards and ARMM reports |
| **Benefits** | 10 | Register benefits (P13), track measurements, detect drift, map dependency networks, cascade impact analysis, forecast realisation, assess maturity |

---

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | For GMPP narratives and review action extraction | Powers AI-generated content |
| `PORT` | For remote server only | HTTP port (default: 8080) |
| `NISTA_CLIENT_ID` | For NISTA API submission | NISTA authentication |
| `NISTA_CLIENT_SECRET` | For NISTA API submission | NISTA authentication |

---

## Troubleshooting

**"No tools showing up"**
- Check the server is running: `pda-platform-server` should start without errors
- Check your config file path is correct for your platform
- Restart your AI client after adding the config

**"Import error on startup"**
- Ensure all packages are installed: `pip install pm-mcp-servers`
- For narrative features: `pip install "agent-task-planning[anthropic]"`
- For mining features: `pip install "agent-task-planning[mining]"`

**"Connection refused" (remote)**
- Check the server is running: `curl http://localhost:8080/health`
- Check your port is not blocked by a firewall
- For Render: check the deploy logs in the Render dashboard

---

## Quick test prompts

Once connected, try these to verify everything works:

- "What PDA Platform tools do you have available?"
- "Load this project file and show me the critical path"
- "Ingest an assumption: construction materials inflation at 2.5% per annum for project DEMO-001"
- "Run a full assurance workflow for project DEMO-001"

---

*PDA Platform is open source: [github.com/antnewman/pda-platform](https://github.com/antnewman/pda-platform)*
