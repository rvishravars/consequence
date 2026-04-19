"""MCP-backed LLM agent (OpenAI-compatible / Gemma)."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import AsyncOpenAI
from mcp import ClientSession

from consequence.types import ToolCallRecord

_DEFAULT_MODEL = "gemma4"
_DEFAULT_BASE_URL = os.environ.get("AGENT_BASE_URL", "http://host.docker.internal:11434/v1")
_MAX_ITERATIONS = 10


def _mcp_tools_to_openai(tools: list[Any]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to OpenAI tool format."""
    result = []
    for tool in tools:
        schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
        result.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": schema,
                },
            }
        )
    return result


async def run_agent(
    session: ClientSession,
    user_message: str,
    system_prompt: str,
    model: str = _DEFAULT_MODEL,
    client: AsyncOpenAI | None = None,
    max_iterations: int = _MAX_ITERATIONS,
) -> tuple[str, list[ToolCallRecord]]:
    """Run an agentic loop against an MCP server using an OpenAI-compatible API.

    Args:
        session: An initialised MCP ``ClientSession``.
        user_message: The user's input message.
        system_prompt: System prompt sent to the LLM.
        model: Model name (e.g. gemma4).
        client: Optional pre-built ``AsyncOpenAI`` client.
        max_iterations: Maximum number of LLM turns before forcing a stop.

    Returns:
        A tuple of (final text reply, list of tool calls made).
    """
    ai_client = client or AsyncOpenAI(base_url=_DEFAULT_BASE_URL, api_key="not-needed")

    tools_response = await session.list_tools()
    openai_tools = _mcp_tools_to_openai(tools_response.tools)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    tool_calls_made: list[ToolCallRecord] = []

    for _ in range(max_iterations):
        response = await ai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools if openai_tools else None,
        )

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content or "", tool_calls_made

        # Handle tool calls
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            tool_result = await session.call_tool(name, args)
            content_parts = tool_result.content or []
            result_text = " ".join(
                c.text for c in content_parts if hasattr(c, "text")
            )

            tool_calls_made.append(
                ToolCallRecord(
                    name=name,
                    arguments=args,
                    result=result_text,
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": result_text,
                }
            )

    return "Max iterations reached without a final answer.", tool_calls_made
