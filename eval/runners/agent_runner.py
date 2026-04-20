"""Isolated runner for the MCP agent."""

import argparse
import asyncio
import json
import logging
import sys
import time
import traceback

from mcp.shared.memory import create_connected_server_and_client_session

from eval.agent import run_agent
from evaluator.types import EvalResult, EvalTask
from evaluator.registry import get_suite, discover_plugins, register_agent

logging.basicConfig(level=logging.WARNING)


@register_agent("default")
def default_runner_command(**kwargs) -> list[str]:
    """Return the command to run the built-in Python agent runner."""
    import sys
    return [sys.executable, "-m", "eval.runners.agent_runner"]


async def main():
    # 1. Read input from Stdin
    input_data = json.loads(sys.stdin.read())
    
    task_dict = input_data["task"]
    model = input_data.get("model", "gemma4")
    suite_name = input_data.get("suite_name", "unknown")
    
    # Reconstruct EvalTask
    task = EvalTask(**task_dict)

    start = time.monotonic()
    
    # 2. Get the server factory from the suite (needed for tools)
    discover_plugins("eval.suites")
    suite = get_suite(suite_name)
    if not suite:
        print(json.dumps({"error": f"Unknown suite: {suite_name}"}))
        sys.exit(1)
        
    server = suite.server_factory()
    
    try:
        async with create_connected_server_and_client_session(server) as session:
            output, tool_calls = await run_agent(
                session=session,
                user_message=task.user_message,
                system_prompt=task.system_prompt,
                model=model,
            )
            
        latency = time.monotonic() - start
        
        result_dict = {
            "task_id": task.id,
            "passed": False,
            "score": 0.0,
            "output": output,
            "tool_calls": [tc.model_dump() for tc in tool_calls],
            "latency_seconds": latency,
            "error": None,
        }
        
        print(json.dumps(result_dict))
        
    except Exception as exc:
        latency = time.monotonic() - start
        error_msg = str(exc)
        if hasattr(exc, "exceptions"): # Handle ExceptionGroup
            error_msg = "; ".join(str(e) for e in exc.exceptions)
            
        print(json.dumps({
            "task_id": task.id,
            "passed": False,
            "score": 0.0,
            "error": error_msg,
            "latency_seconds": latency,
            "traceback": traceback.format_exc()
        }))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
