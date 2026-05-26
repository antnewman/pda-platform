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

# Audit finding P5.F07. Bootstrap progress is now emitted via the
# stdlib logger so it appears in structured logs alongside the rest of
# the platform's output, with a relative timestamp tag for cold-start
# diagnostics. A duplicate stderr print is kept for the very first
# event so an operator inspecting raw stderr on Render still sees the
# process is alive — the logger may not yet be configured at this
# point in import time.
_IMPORT_T0 = time.time()
_bootstrap_logger = logging.getLogger("pda_platform.bootstrap")
if not _bootstrap_logger.handlers:
    _bootstrap_handler = logging.StreamHandler(stream=sys.stderr)
    _bootstrap_handler.setFormatter(
        logging.Formatter(
            "[pda-platform-remote] T+%(rel_seconds).2fs phase=%(phase)s %(message)s"
        )
    )
    _bootstrap_logger.addHandler(_bootstrap_handler)
    _bootstrap_logger.setLevel(logging.INFO)


def _log_bootstrap_phase(phase: str, message: str) -> None:
    """Emit a structured bootstrap log line with a relative timestamp.

    Replaces the legacy stderr ``print()`` calls flagged in audit
    finding P5.F07. The ``rel_seconds`` extra is wall-clock seconds
    since first-import so operators can spot slow imports without
    correlating absolute timestamps.
    """
    _bootstrap_logger.info(
        message,
        extra={"rel_seconds": time.time() - _IMPORT_T0, "phase": phase},
    )


_log_bootstrap_phase("imports.start", "starting imports")

from pathlib import Path  # noqa: E402
from mcp.server.sse import SseServerTransport  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import FileResponse, JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402

_log_bootstrap_phase("imports.transport_ok", "transport and web imports ok")

from .server import ALL_TOOLS, server  # noqa: E402
from ..pm_assumptions.server import build_assumption_dashboard_panels  # noqa: E402
from .. import _audit  # noqa: E402

_log_bootstrap_phase(
    "imports.tools_loaded", f"loaded {len(ALL_TOOLS)} tools"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Audit finding P5.F06. The platform falls back to evidence-only mode
# when ``ANTHROPIC_API_KEY`` is absent. Operators should learn this at
# deploy time, not at the first call to a Claude-authored tool.
if not os.environ.get("ANTHROPIC_API_KEY"):
    _log_bootstrap_phase(
        "config.anthropic_missing",
        "ANTHROPIC_API_KEY not set; AI-authored tools will use "
        "evidence-only fallback (audit finding P5.F06).",
    )

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
        # Audit finding P5.F04 — chain size per module so a growing
        # JSONL backlog is visible without parsing the files.
        "audit_chain_size_bytes": _audit.chain_sizes(),
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
