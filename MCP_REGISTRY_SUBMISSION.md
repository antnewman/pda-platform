# MCP Registry Submission Guide

**Date:** 2026-01-04
**Status:** Ready for submission after PyPI v0.3.0 publish

## Overview

The MCP Registry submission process has modernized from the PR-based approach to using the `mcp-publisher` CLI tool. This document outlines the updated process for submitting the three PDA Task Force servers.

## Changes Made

✅ **Completed:**
1. Added MCP verification comments to README.md (required for PyPI package validation)
2. Version bumped to 0.3.0 in pyproject.toml
3. All code committed and pushed to GitHub as antnewman

## Next Steps Required

### Step 1: Publish to PyPI v0.3.0

Before submitting to the MCP Registry, the package must be published to PyPI with the verification comments:

```bash
cd packages/pm-mcp-servers

# Build distribution
python -m build

# Publish to PyPI (requires PyPI authentication)
python -m twine upload dist/pm_mcp_servers-0.3.0*
```

**Note:** You'll need PyPI credentials. If not set up:
```bash
# Configure PyPI token
pip install twine
python -m twine upload --repository pypi dist/*
```

### Step 2: Install mcp-publisher CLI

```bash
# Windows (PowerShell)
$arch = if ([System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -eq "Arm64") { "arm64" } else { "amd64" }
Invoke-WebRequest -Uri "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_$arch.tar.gz" -OutFile "mcp-publisher.tar.gz"
tar xf mcp-publisher.tar.gz mcp-publisher.exe
rm mcp-publisher.tar.gz
# Move mcp-publisher.exe to a directory in your PATH

# Verify installation
mcp-publisher --help
```

### Step 3: Create server.json Files

Create three `server.json` files (one for each server):

#### pm-data-server.json

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.antnewman/pm-data",
  "title": "Project Management Data Tools",
  "description": "Parse, convert, and query project management data from 8 formats (MSPDI, P6 XER, NISTA, Jira, Monday, Asana, Smartsheet, GMPP) via a unified canonical model. Part of the PDA Task Force open source platform.",
  "repository": {
    "url": "https://github.com/PDA-Task-Force/pda-platform",
    "source": "github"
  },
  "version": "0.3.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "pm-mcp-servers",
      "version": "0.3.0",
      "transport": {
        "type": "stdio"
      },
      "environmentVariables": []
    }
  ]
}
```

#### pm-validate-server.json

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.antnewman/pm-validate",
  "title": "Project Management Validation",
  "description": "Validate project data against NISTA standards, scheduling best practices, and custom rule sets. Includes compliance checking for UK government Programme and Project Data Standard. Part of the PDA Task Force platform.",
  "repository": {
    "url": "https://github.com/PDA-Task-Force/pda-platform",
    "source": "github"
  },
  "version": "0.3.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "pm-mcp-servers",
      "version": "0.3.0",
      "transport": {
        "type": "stdio"
      },
      "environmentVariables": []
    }
  ]
}
```

#### pm-analyse-server.json

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.antnewman/pm-analyse",
  "title": "Project Management AI Analysis",
  "description": "AI-powered project analysis with confidence scoring and evidence trails. Includes risk identification, completion forecasting (EVM, Monte Carlo, Reference Class), outlier detection, health assessment, and mitigation generation. Part of the PDA Task Force platform.",
  "repository": {
    "url": "https://github.com/PDA-Task-Force/pda-platform",
    "source": "github"
  },
  "version": "0.3.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "pm-mcp-servers",
      "version": "0.3.0",
      "transport": {
        "type": "stdio"
      },
      "environmentVariables": []
    }
  ]
}
```

### Step 4: Authenticate with MCP Registry

```bash
# Authenticate using GitHub
mcp-publisher login github
```

Follow the prompts to authenticate via GitHub device flow.

### Step 5: Publish Each Server

```bash
# Publish pm-data
cd /path/to/pm-data-server.json/directory
mcp-publisher publish --file pm-data-server.json

# Publish pm-validate
mcp-publisher publish --file pm-validate-server.json

# Publish pm-analyse
mcp-publisher publish --file pm-analyse-server.json
```

### Step 6: Verify Publication

```bash
# Check pm-data
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.antnewman/pm-data"

# Check pm-validate
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.antnewman/pm-validate"

# Check pm-analyse
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.antnewman/pm-analyse"
```

## Verification Requirements

The MCP Registry verifies PyPI package ownership by checking for the MCP name comments in the package README. We've added:

```markdown
<!-- mcp-name: io.github.antnewman/pm-data -->
<!-- mcp-name: io.github.antnewman/pm-validate -->
<!-- mcp-name: io.github.antnewman/pm-analyse -->
```

These are now in the README.md and will be included when publishing v0.3.0 to PyPI.

## Benefits of Registry Submission

1. **Discoverability:** Servers appear in the official MCP Registry at https://registry.modelcontextprotocol.io/
2. **Trust Signal:** Official registration validates provenance and ownership
3. **Integration:** Claude Desktop and other MCP clients can discover and install servers automatically
4. **Documentation:** Creates timestamped public record of server capabilities

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Registry validation failed for package" | Ensure README contains MCP name comments and v0.3.0 is published to PyPI |
| "Invalid or expired Registry JWT token" | Re-run `mcp-publisher login github` |
| "You do not have permission to publish" | Verify GitHub authentication and that server names start with `io.github.antnewman/` |

## References

- MCP Registry Documentation: https://github.com/modelcontextprotocol/registry/tree/main/docs
- PyPI Package Types Guide: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/package-types.mdx
- Quickstart Guide: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx

## Status Summary

| Item | Status |
|------|--------|
| MCP verification comments added | ✅ Complete |
| Version 0.3.0 set | ✅ Complete |
| PyPI v0.3.0 published | ✅ Complete |
| mcp-publisher installed | ✅ Complete |
| server.json files created | ✅ Complete |
| Registry authentication | ✅ Complete |
| Servers published | ✅ Complete |

## Publication Results

All three servers successfully published to the MCP Registry on 2026-01-04:

- **pm-data**: Published at 20:50:31 UTC
- **pm-validate**: Published at 20:50:46 UTC
- **pm-analyse**: Published at 20:50:55 UTC

All servers are now discoverable at https://registry.modelcontextprotocol.io/ and can be installed by Claude Desktop and other MCP clients.

---

**Status:** COMPLETE - All servers successfully registered with the MCP Registry.
