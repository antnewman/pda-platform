"""PDA Platform — remote HTTP server with SSE transport.

Wraps the unified pda-platform MCP server in an SSE transport layer
so it can be accessed remotely from Claude.ai or any MCP client over HTTP.

Usage:
    pda-platform-remote              # starts on $PORT or 8080
    PORT=3000 pda-platform-remote    # custom port

Endpoints:
    GET  /sse                              SSE connection endpoint (MCP client connects here)
    POST /messages                         Message endpoint (MCP client sends tool calls here)
    GET  /health                           Health check for Render/Railway
    GET  /data/{project_id}/dashboard.json Live assumption dashboard panel data (for UDS)
    GET  /dashboards/{name}.uds.yaml       UDS dashboard spec file served by the platform
"""

from __future__ import annotations

import logging
import os
import sys

# Print to stderr immediately so Render logs show we've started, even if
# later imports fail. This helps diagnose silent import crashes.
print("[pda-platform-remote] starting imports...", file=sys.stderr, flush=True)

from pathlib import Path  # noqa: E402
from mcp.server.sse import SseServerTransport  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import FileResponse, JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402

print("[pda-platform-remote] transport/web imports ok", file=sys.stderr, flush=True)

from .server import ALL_TOOLS, server  # noqa: E402
from ..pm_assumptions.server import build_assumption_dashboard_panels  # noqa: E402

print(f"[pda-platform-remote] loaded {len(ALL_TOOLS)} tools", file=sys.stderr, flush=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sse = SseServerTransport("/messages")


async def handle_sse(request: Request):
    """Handle SSE connection from MCP client."""
    logger.info("SSE connection from %s", request.client)
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


async def handle_messages(request: Request):
    """Handle POST messages from MCP client."""
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health(request: Request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "server": "pda-platform",
        "tools": len(ALL_TOOLS),
        "transport": "sse",
    })


# Directory containing UDS dashboard YAML specs shipped with pm-assumptions.
# Resolved once at import time. Located at:
#   packages/pm-mcp-servers/src/pm_mcp_servers/pm_assumptions/dashboards/
_DASHBOARD_SPECS_DIR = (
    Path(__file__).resolve().parent.parent / "pm_assumptions" / "dashboards"
)


async def get_dashboard_data(request: Request):
    """GET /data/{project_id}/dashboard.json — live UDS panel data.

    Returns fresh panel JSON for the assumption dashboard, assembled on
    every request from the current AssuranceStore state. Designed to be
    polled by a UDS renderer running elsewhere (e.g. hosted on Netlify).
    """
    project_id = request.path_params["project_id"]
    try:
        panels = build_assumption_dashboard_panels(project_id)
        return JSONResponse(panels)
    except Exception as exc:
        logger.exception("Failed to build dashboard data for %s", project_id)
        return JSONResponse({"error": str(exc)}, status_code=400)


async def get_dashboard_spec(request: Request):
    """GET /dashboards/{name}.uds.yaml — UDS dashboard spec served by the platform.

    The platform ships its own dashboard specs alongside the modules they
    describe, so the UDS renderer can load spec and data from the same
    origin. Spec files live in pm_assumptions/dashboards/.
    """
    name = request.path_params["name"]
    # Strip .uds.yaml if included in the path param and reject path traversal
    name = name.replace(".uds.yaml", "").replace("/", "").replace("\\", "").replace("..", "")
    candidate = _DASHBOARD_SPECS_DIR / f"{name}.uds.yaml"
    if not candidate.is_file():
        return JSONResponse(
            {"error": f"Dashboard spec '{name}' not found"},
            status_code=404,
        )
    return FileResponse(candidate, media_type="application/x-yaml")


app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=health),
        Route(
            "/data/{project_id}/dashboard.json",
            endpoint=get_dashboard_data,
            methods=["GET"],
        ),
        Route(
            "/dashboards/{name}.uds.yaml",
            endpoint=get_dashboard_spec,
            methods=["GET"],
        ),
    ],
)

# CORS — permissive for demo use. The HTTP endpoints serve public,
# read-only project data with no authentication, so origin restrictions
# are unnecessary and would only hamper legitimate use (e.g. Netlify-
# hosted UDS renderers, Claude.ai integrations).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


def main() -> None:
    """Entry point for pda-platform-remote."""
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting PDA Platform remote server on port %d", port)
    logger.info("SSE endpoint: /sse")
    logger.info("Tools available: %d", len(ALL_TOOLS))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
