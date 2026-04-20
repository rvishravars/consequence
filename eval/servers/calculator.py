"""A simple calculator MCP server for use in evaluations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def make_calculator_server() -> FastMCP:
    """Return a fresh FastMCP server that exposes basic arithmetic tools."""
    mcp = FastMCP("calculator")

    @mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b

    return mcp
