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

    @mcp.tool()
    def subtract(a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b

    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    @mcp.tool()
    def divide(a: float, b: float) -> float:
        """Divide a by b.  Raises ValueError when b is zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    @mcp.tool()
    def power(base: float, exponent: float) -> float:
        """Raise base to the given exponent."""
        return base**exponent

    return mcp
