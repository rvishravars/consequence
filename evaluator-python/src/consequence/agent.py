"""MCP-backed LLM agent (Anthropic Claude)."""

from __future__ import annotations

import json
from typing import Any

import anthropic
from mcp import ClientSession

from consequence.types import ToolCallRecord

_DEFAULT_MODEL = "claude-3-5-haiku-20241022"
_MAX_ITERATIONS = 10


def _mcp_tools_to_anthropic(tools: list[Any]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to Anthropic tool format."""
    result = []
    for tool in tools:
        schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
        result.append(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": schema,
            }
        )
    return result


async def run_agent(
    session: ClientSession,
    user_message: str,
    system_prompt: str,
    model: str = _DEFAULT_MODEL,
    anthropic_client: anthropic.AsyncAnthropic | None = None,
    max_iterations: int = _MAX_ITERATIONS,
) -> tuple[str, list[ToolCallRecord]]:
    """Run an agentic loop against an MCP server and return the final reply.

    Args:
        session: An initialised MCP ``ClientSession``.
        user_message: The user's input message.
        system_prompt: System prompt sent to the LLM.
        model: Anthropic model name.
        anthropic_client: Optional pre-built ``AsyncAnthropic`` client.
        max_iterations: Maximum number of LLM turns before forcing a stop.

    Returns:
        A tuple of (final text reply, list of tool calls made).
    """
    client = anthropic_client or anthropic.AsyncAnthropic()

    tools_response = await session.list_tools()
    anthropic_tools = _mcp_tools_to_anthropic(tools_response.tools)

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    tool_calls_made: list[ToolCallRecord] = []

    for _ in range(max_iterations):
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=anthropic_tools,
            messages=messages,
        )

        # Append assistant turn to conversation
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text reply
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text, tool_calls_made
            return "", tool_calls_made

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_result = await session.call_tool(block.name, block.input or {})
                content_parts = tool_result.content or []
                result_text = " ".join(
                    c.text for c in content_parts if hasattr(c, "text")
                )

                tool_calls_made.append(
                    ToolCallRecord(
                        name=block.name,
                        arguments=block.input or {},
                        result=result_text,
                    )
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    }
                )

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason – return whatever text is available
        for block in response.content:
            if hasattr(block, "text"):
                return block.text, tool_calls_made
        return "", tool_calls_made

    return "Max iterations reached without a final answer.", tool_calls_made
