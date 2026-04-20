"""SSE Transport implementation for remote MCP agents."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.sse import SseServerTransport
from starlette.responses import Response
from starlette.requests import Request
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mcp")

# Active SSE sessions: session_id -> SseServerTransport
_sessions: dict[str, SseServerTransport] = {}


@router.get("/sse/{session_id}")
async def handle_sse(session_id: str, request: Request):
    """Establish an SSE connection for a specific evaluation session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    transport = _sessions[session_id]
    async with transport.connect_sse(request.scope, request.receive, request._send) as sse:
        await sse.handle_sse_request()


@router.post("/messages/{session_id}")
async def handle_message(session_id: str, request: Request):
    """Handle incoming MCP messages for an active session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    transport = _sessions[session_id]
    await transport.handle_post_message(request.scope, request.receive, request._send)
    return Response(status_code=202)


def register_transport(session_id: str, transport: SseServerTransport):
    """Register a transport instance for a new session."""
    _sessions[session_id] = transport


def unregister_transport(session_id: str):
    """Remove a transport instance when a session is closed."""
    _sessions.pop(session_id, None)
