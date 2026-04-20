"""MCP-backed LLM agent (OpenAI-compatible / Gemma)."""

from __future__ import annotations

import json
import os
from typing import Any
from functools import partial

from pydantic import BaseModel, create_model

from mcp import ClientSession
from evaluator.types import ToolCallRecord
from evaluator.registry import register_agent

# Langchain imports
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

_DEFAULT_MODEL = "gemma4"
_DEFAULT_BASE_URL = os.environ.get("AGENT_BASE_URL", "http://host.docker.internal:11434/v1")
_MAX_ITERATIONS = 10


def _create_dynamic_pydantic_model(schema: dict) -> type[BaseModel]:
    """Convert an MCP inputSchema/JSONSchema into a Pydantic V2 model for LangChain tooling."""
    fields = {}
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    
    for name, prop in properties.items():
        type_str = prop.get("type", "string")
        ptype = str
        if type_str == "integer": ptype = int
        elif type_str == "boolean": ptype = bool
        elif type_str == "number": ptype = float
        elif type_str == "array": ptype = list
        elif type_str == "object": ptype = dict
            
        if name in required:
            fields[name] = (ptype, ...)
        else:
            fields[name] = (ptype, None)
            
    return create_model("DynamicToolArgs", **fields)


async def _execute_mcp_tool(tool_name: str, session: ClientSession, **kwargs) -> str:
    """The generic executor that maps LangChain operations into the active MCP session."""
    try:
        result = await session.call_tool(tool_name, kwargs)
        content_parts = result.content or []
        return " ".join(c.text for c in content_parts if hasattr(c, "text"))
    except Exception as e:
        return f"Error executing tool {tool_name}: {e}"


@register_agent("default")
async def run_agent(
    session: ClientSession,
    user_message: str,
    system_prompt: str,
    model: str = _DEFAULT_MODEL,
    client: Any | None = None,  # Kept parameter for API compat
    max_iterations: int = _MAX_ITERATIONS,
) -> tuple[str, list[ToolCallRecord]]:
    """Run an agentic loop against an MCP server using LangChain."""
    
    # 1. Fetch live MCP Tools and map to LangChain StructuredTool schema
    tools_response = await session.list_tools()
    lc_tools = []
    
    for mcp_tool in tools_response.tools:
        schema = getattr(mcp_tool, "inputSchema", {})
        pydantic_model = _create_dynamic_pydantic_model(schema)
        
        # We partially bind the name and session so each tool calls its own MCP endpoint
        tool_func = partial(_execute_mcp_tool, mcp_tool.name, session)
        tool_func.__name__ = mcp_tool.name.replace("-", "_")
        
        lc_tool = StructuredTool(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            args_schema=pydantic_model,
            coroutine=tool_func,
        )
        lc_tools.append(lc_tool)

    # 2. Configure LangChain OpenAI integration (to hit Ollama backend)
    # Important: max_retries ensures we catch and resubmit broken payloads
    llm = ChatOpenAI(
        model=model, 
        base_url=_DEFAULT_BASE_URL, 
        api_key="not-needed",
        max_retries=3
    )

    # 3. Construct the Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, lc_tools, prompt)
    
    executor = AgentExecutor(
        agent=agent, 
        tools=lc_tools, 
        return_intermediate_steps=True,
        max_iterations=max_iterations,
        handle_parsing_errors=True
    )

    # 4. Invoke the chain!
    # A cool trick: if it fails with an Exception, it will safely bubble up and mark failed orchestrator jobs
    response = await executor.ainvoke({"input": user_message})

    # 5. Extract reports for Consequence Framework
    output_text = response.get("output", "")
    
    records = []
    for action, result in response.get("intermediate_steps", []):
        records.append(ToolCallRecord(
            name=action.tool,
            arguments=action.tool_input,
            result=str(result)
        ))

    return output_text, records
