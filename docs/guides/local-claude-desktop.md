# Connecting Claude Desktop to a Local PDA Platform Install

This guide explains how to run PDA Platform on your own machine and connect it to Claude Desktop. The local installation is faster than the remote endpoint, works without an internet connection (except for AI-powered tools), and keeps all project data on your machine.

---

## Prerequisites

- Claude Desktop installed ([claude.ai/download](https://claude.ai/download))
- Python 3.11 or later
- pip

---

## Step 1: Install the MCP Server Package

Open a terminal and install the `pm-mcp-servers` package:

```bash
pip install pm-mcp-servers
```

To enable the AI-powered assurance tools (review action extraction, recurrence detection, narrative generation), also install:

```bash
pip install "agent-task-planning[anthropic]"
```

For recurrence detection using sentence-transformer embeddings:

```bash
pip install "agent-task-planning[mining]"
```

---

## Step 2: Edit the Claude Desktop Config File

Locate the Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Open the file in a text editor and add the PDA Platform server to the `mcpServers` object. If the file does not exist, create it with the content below.

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

Replace `sk-ant-...` with your Anthropic API key. If you do not have an Anthropic API key, omit the `env` block — data parsing, validation, and non-AI assurance tools will still work; only `track_review_actions` and `generate_narrative` require it.

---

## Step 3: Restart Claude Desktop

Fully quit Claude Desktop (not just close the window) and relaunch it. On macOS, right-click the Claude icon in the Dock and select Quit. On Windows, right-click the Claude icon in the system tray and select Quit.

After restarting, Claude Desktop will start the `pda-platform-server` process and register the tools.

---

## Step 4: Verify the Connection

In a new Claude Desktop conversation, type:

> "What PDA tools do you have available?"

Claude should respond with a summary of the 126 tools across the 18 modules. If you see no tools or an error, check that `pda-platform-server` is on your system PATH by running `pda-platform-server --help` in a terminal.

---

## Step 5: Your First Prompt

Once the connection is confirmed, try a simple validation:

> "Validate this project against NISTA requirements."

Or, if you have a project file on disk:

> "Load /path/to/schedule.mpp and show me the critical path."

For a fuller walkthrough using synthetic project data, see [first-project.md](first-project.md).

---

## Troubleshooting

**"Command not found: pda-platform-server"**
The package was not installed into a Python environment that is on your PATH. Try `pip install --user pm-mcp-servers` or activate the virtual environment where you installed the package before relaunching Claude Desktop.

**"0 tools available"**
Claude Desktop may have failed to start the server. Check the Claude Desktop logs (Help > Open Logs Folder) for startup errors.

**AI tools not working**
Confirm that `ANTHROPIC_API_KEY` is set correctly in the config file and that the key is active. The non-AI tools will continue to function without it.
