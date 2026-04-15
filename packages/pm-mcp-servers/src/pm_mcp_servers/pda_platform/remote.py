"""PDA Platform — remote HTTP server with SSE transport.

Wraps the unified pda-platform MCP server in an SSE transport layer
so it can be accessed remotely from Claude.ai or any MCP client over HTTP.

Usage:
    pda-platform-remote              # starts on $PORT or 8080
    PORT=3000 pda-platform-remote    # custom port

Endpoints:
    GET  /sse          SSE connection endpoint (MCP client connects here)
    POST /messages     Message endpoint (MCP client sends tool calls here)
    GET  /health       Health check for Render/Railway
"""

from __future__ import annotations

import logging
import os
import sys

# Print to stderr immediately so Render logs show we've started, even if
# later imports fail. This helps diagnose silent import crashes.
print("[pda-platform-remote] starting imports...", file=sys.stderr, flush=True)

from mcp.server.sse import SseServerTransport  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402

print("[pda-platform-remote] transport/web imports ok", file=sys.stderr, flush=True)

from .server import ALL_TOOLS, server  # noqa: E402

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


app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        Route("/health", endpoint=health),
    ],
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
