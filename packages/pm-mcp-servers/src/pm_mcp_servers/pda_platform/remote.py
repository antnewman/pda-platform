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
import time

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
from .. import _audit  # noqa: E402

print(f"[pda-platform-remote] loaded {len(ALL_TOOLS)} tools", file=sys.stderr, flush=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wall-clock at first-import — used by /health for an uptime indicator
# (audit finding P5.F08).
_STARTED_AT = time.time()

# Dashboard endpoints (`/data/*`, `/dashboards/*`) are protected by an
# optional shared-secret token (audit finding P4.F02). When
# `PDA_DASHBOARD_TOKEN` is set, both endpoints require it via either
# `Authorization: Bearer <token>` or `?token=` query string. When unset,
# the endpoints remain open (current demo posture) but a startup
# warning makes the choice operator-visible.
_DASHBOARD_TOKEN = os.environ.get("PDA_DASHBOARD_TOKEN") or None
if not _DASHBOARD_TOKEN:
    print(
        "[pda-platform-remote] WARNING: PDA_DASHBOARD_TOKEN not set; "
        "/data and /dashboards endpoints are publicly accessible "
        "(audit finding P4.F02).",
        file=sys.stderr,
        flush=True,
    )


def _request_authorised(request: Request) -> bool:
    """Return True if the request bears the configured dashboard token.

    When no token is configured the endpoint is open by design (demo
    posture); see startup warning above. When a token is configured the
    request must supply it via `Authorization: Bearer <token>` or
    `?token=<token>`.
    """
    if not _DASHBOARD_TOKEN:
        return True
    header = request.headers.get("authorization", "")
    if header.startswith("Bearer "):
        supplied = header[len("Bearer "):].strip()
        if supplied == _DASHBOARD_TOKEN:
            return True
    query_token = request.query_params.get("token")
    if query_token and query_token == _DASHBOARD_TOKEN:
        return True
    return False


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
    """Health check endpoint.

    Deepened in response to audit finding P5.F02: a simple
    ``status: ok`` reveals nothing about realistic degradation modes
    (missing API key, audit-chain failure, lost store connectivity).
    The expanded shape lets operators alert on each individually.

    Fields:
      * ``status``: liveness indicator (``ok`` while the process can
        respond — does not assert downstream readiness).
      * ``server``, ``tools``, ``transport``: previously-shipped.
      * ``uptime_seconds``: integer seconds since import (P5.F08).
      * ``anthropic_api_key_present``: boolean. ``false`` means every
        AI-authored tool will fall back to evidence-only output
        (P5.F06).
      * ``audit_failure_count``: per-module count of swallowed
        :func:`safe_record_decision` failures since process start
        (P5.F01). Alert if non-zero — silent audit-chain failure was
        the dominant cross-pass finding.
      * ``dashboard_token_required``: ``true`` once
        ``PDA_DASHBOARD_TOKEN`` is configured (P4.F02).
    """
    return JSONResponse({
        "status": "ok",
        "server": "pda-platform",
        "tools": len(ALL_TOOLS),
        "transport": "sse",
        "uptime_seconds": int(time.time() - _STARTED_AT),
        "anthropic_api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "audit_signing_key_present": bool(
            os.environ.get("PDA_AUDIT_SIGNING_KEY")
        ),
        "dashboard_token_required": bool(_DASHBOARD_TOKEN),
        "audit_failure_count": _audit.failure_stats(),
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

    Auth (audit finding P4.F02): when ``PDA_DASHBOARD_TOKEN`` is set,
    requests must supply it via ``Authorization: Bearer`` or ``?token=``.
    When unset, the endpoint remains open and a startup warning is
    emitted.
    """
    if not _request_authorised(request):
        return JSONResponse({"error": "unauthorised"}, status_code=401)
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

    Auth: same `PDA_DASHBOARD_TOKEN` gate as `/data/*` (P4.F02).
    """
    if not _request_authorised(request):
        return JSONResponse({"error": "unauthorised"}, status_code=401)
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
