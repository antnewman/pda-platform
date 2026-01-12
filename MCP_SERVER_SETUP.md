# PM-NISTA MCP Server Setup Guide

## ✅ Server Registered

The pm-nista MCP server has been registered in Claude Desktop at:
```
C:\Users\antjs\AppData\Roaming\Claude\claude_desktop_config.json
```

## 📋 Configuration Steps

### Step 1: Install Dependencies

```bash
cd C:\Users\antjs\pda-platform

# Install pm-data-tools with NISTA integration
cd packages\pm-data-tools
pip install -e .

# Install agent-task-planning (for AI narratives)
cd ..\agent-task-planning
pip install -e .

# Install pm-mcp-servers
cd ..\pm-mcp-servers
pip install -e .
```

### Step 2: Configure Environment Variables

Edit the Claude Desktop config file and add your API credentials:

**File**: `C:\Users\antjs\AppData\Roaming\Claude\claude_desktop_config.json`

Add these environment variables to the `"env"` section:

```json
{
  "mcpServers": {
    "pm-nista": {
      "command": "python",
      "args": ["-m", "pm_mcp_servers.pm_nista.server"],
      "cwd": "C:\\Users\\antjs\\pda-platform",
      "env": {
        "PYTHONPATH": "C:\\Users\\antjs\\pda-platform\\packages\\pm-data-tools\\src;C:\\Users\\antjs\\pda-platform\\packages\\agent-task-planning\\src;C:\\Users\\antjs\\pda-platform\\packages\\pm-mcp-servers\\src",
        "NISTA_ENVIRONMENT": "sandbox",
        "NISTA_API_URL": "https://api-sandbox.nista.gov.uk/v1",

        "ANTHROPIC_API_KEY": "sk-ant-YOUR_API_KEY_HERE",
        "NISTA_CLIENT_ID": "your_nista_client_id",
        "NISTA_CLIENT_SECRET": "your_nista_client_secret"
      }
    }
  }
}
```

**Optional** (for mTLS):
```json
"NISTA_CERT_PATH": "C:\\path\\to\\client-cert.pem",
"NISTA_KEY_PATH": "C:\\path\\to\\private-key.pem"
```

### Step 3: Restart Claude Desktop

After installing dependencies and configuring environment variables:

1. **Close Claude Desktop completely** (check system tray)
2. **Reopen Claude Desktop**
3. The pm-nista server will start automatically

### Step 4: Verify Server is Running

In Claude Desktop, try using one of these tools:

**Tool 1: Validate a GMPP Report**
```
Use the validate_gmpp_report tool to validate a quarterly report
```

**Tool 2: Generate a Narrative**
```
Use the generate_narrative tool to create a DCA narrative for a test project
```

**Tool 3: Generate Full GMPP Report**
```
Use the generate_gmpp_report tool with a project file
```

## 🔧 Available Tools

### 1. `generate_gmpp_report`
Generate complete GMPP quarterly report from project file

**Parameters:**
- `project_file`: Path to project file (MS Project, GMPP CSV, etc.)
- `quarter`: Q1, Q2, Q3, or Q4
- `financial_year`: Format "2025-26"
- `generate_narratives`: true/false (requires ANTHROPIC_API_KEY)

**Example:**
```
Generate a GMPP quarterly report for Q2 2025-26 from the project file at C:\Users\antjs\pda-platform\tests\fixtures\gmpp\projects.csv
```

### 2. `generate_narrative`
Generate AI-powered narrative with confidence scoring

**Parameters:**
- `narrative_type`: dca, cost, schedule, benefits, or risk
- `project_context`: Object with project data

**Example:**
```
Generate a DCA narrative for High Speed Rail Phase 2 with AMBER rating
```

### 3. `submit_to_nista`
Submit GMPP quarterly return to NISTA API

**Parameters:**
- `report_file`: Path to quarterly report JSON file
- `project_id`: Project identifier
- `environment`: sandbox or production

**Example:**
```
Submit the quarterly report at report.json to NISTA sandbox for project DFT-HSR-001
```

### 4. `fetch_nista_metadata`
Fetch project metadata from NISTA master registry

**Parameters:**
- `project_id`: NISTA project code or internal project ID
- `environment`: sandbox or production

**Example:**
```
Fetch project metadata from NISTA for project DFT_0123_2025-Q2
```

### 5. `validate_gmpp_report`
Validate GMPP quarterly report against NISTA requirements

**Parameters:**
- `report_file`: Path to quarterly report JSON file
- `strictness`: LENIENT, STANDARD, or STRICT

**Example:**
```
Validate the GMPP report at report.json with STANDARD strictness
```

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PYTHONPATH` | ✅ Yes | Python module paths | (auto-configured) |
| `NISTA_ENVIRONMENT` | ✅ Yes | NISTA environment | `sandbox` or `production` |
| `NISTA_API_URL` | ✅ Yes | NISTA API base URL | `https://api-sandbox.nista.gov.uk/v1` |
| `ANTHROPIC_API_KEY` | ⚠️ For AI | Anthropic API key | `sk-ant-...` |
| `NISTA_CLIENT_ID` | ⚠️ For submit | OAuth client ID | From NISTA |
| `NISTA_CLIENT_SECRET` | ⚠️ For submit | OAuth client secret | From NISTA |
| `NISTA_CERT_PATH` | ❌ Optional | Client certificate | `/path/to/cert.pem` |
| `NISTA_KEY_PATH` | ❌ Optional | Private key | `/path/to/key.pem` |

**Note**:
- ✅ Required for server to start
- ⚠️ Required for specific features (narrative generation, submission)
- ❌ Optional (for enhanced security with mTLS)

## 🧪 Testing Without NISTA Credentials

You can test most features without NISTA API credentials:

1. **Generate GMPP Reports** (without AI narratives):
   ```json
   "generate_narratives": false
   ```

2. **Validate Reports**:
   Uses local validation, no API needed

3. **Generate Narratives**:
   Only requires `ANTHROPIC_API_KEY`

4. **Submit to NISTA** and **Fetch Metadata**:
   Require NISTA API credentials

## 🐛 Troubleshooting

### Server Not Appearing in Claude Desktop

1. Check the config file exists:
   ```bash
   cat "$APPDATA/Claude/claude_desktop_config.json"
   ```

2. Check JSON syntax is valid (no trailing commas, proper quotes)

3. Restart Claude Desktop completely

### Import Errors

If you see "No module named 'pm_data_tools'" or similar:

1. Verify PYTHONPATH is set correctly in config
2. Ensure all packages are installed with `pip install -e .`
3. Check Python version is 3.10+:
   ```bash
   python --version
   ```

### API Key Errors

If you see "ANTHROPIC_API_KEY not set":

1. Add your API key to the `env` section in config
2. Restart Claude Desktop
3. Try again

### NISTA Authentication Errors

If you see "NISTA authentication not configured":

1. Add `NISTA_CLIENT_ID` and `NISTA_CLIENT_SECRET` to config
2. Verify credentials are correct for your environment (sandbox/production)
3. Check certificate paths if using mTLS

## 📚 Additional Resources

- **Full Documentation**: See `NISTA_INTEGRATION_COMPLETE.md`
- **Implementation Plan**: See `C:\Users\antjs\.claude\plans\structured-brewing-kazoo.md`
- **Test Examples**: See `packages/pm-data-tools/tests/test_gmpp/test_models.py`
- **MCP Server Code**: See `packages/pm-mcp-servers/src/pm_mcp_servers/pm_nista/server.py`

## ✅ Quick Start Checklist

- [ ] Install all dependencies (`pip install -e .` for each package)
- [ ] Add `ANTHROPIC_API_KEY` to config (for narrative generation)
- [ ] Add NISTA credentials to config (if submitting to NISTA)
- [ ] Restart Claude Desktop
- [ ] Test with `validate_gmpp_report` tool
- [ ] Try generating a narrative
- [ ] Generate a complete GMPP report

Your pm-nista MCP server is ready to use! 🚀
