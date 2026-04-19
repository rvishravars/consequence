"""Evaluation engine: runs tasks against MCP-backed agents."""

from __future__ import annotations

import time
from typing import Any, Callable, Coroutine

import anyio
import anthropic
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

from consequence.agent import run_agent
from consequence.metrics import combined_score
from consequence.types import EvalResult, EvalTask, SuiteReport

_DEFAULT_PASS_THRESHOLD = 0.5


async def run_eval(
    task: EvalTask,
    server: FastMCP,
    anthropic_client: anthropic.AsyncAnthropic | None = None,
    model: str = "claude-3-5-haiku-20241022",
    pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
) -> EvalResult:
    """Run a single :class:`EvalTask` against an MCP server.

    Args:
        task: The evaluation task to run.
        server: A :class:`~mcp.server.fastmcp.FastMCP` server with the tools
            the agent should use.
        anthropic_client: Optional pre-built Anthropic client.
        model: The Anthropic model identifier.
        pass_threshold: Minimum score (0–1) to mark a result as passed.

    Returns:
        An :class:`EvalResult` with score, tool call records, and output.
    """
    start = time.monotonic()
    try:
        async with create_connected_server_and_client_session(server) as session:
            output, tool_calls = await run_agent(
                session=session,
                user_message=task.user_message,
                system_prompt=task.system_prompt,
                model=model,
                anthropic_client=anthropic_client,
            )
    except Exception as exc:  # noqa: BLE001
        latency = time.monotonic() - start
        return EvalResult(
            task_id=task.id,
            passed=False,
            score=0.0,
            error=str(exc),
            latency_seconds=latency,
        )

    latency = time.monotonic() - start
    result = EvalResult(
        task_id=task.id,
        passed=False,
        score=0.0,
        output=output,
        tool_calls=tool_calls,
        latency_seconds=latency,
    )

    # Score the result
    if task.evaluator is not None:
        score = task.evaluator(result)
    else:
        score = combined_score(result, task)

    result.score = max(0.0, min(1.0, score))
    result.passed = result.score >= pass_threshold
    return result


class EvalSuite:
    """A named collection of :class:`EvalTask` objects sharing an MCP server.

    Args:
        name: Human-readable name for the suite.
        server_factory: Zero-argument callable that returns a fresh
            :class:`~mcp.server.fastmcp.FastMCP` server instance.  Called
            once per :meth:`run` invocation so that each run starts clean.
        tasks: Initial list of tasks.
    """

    def __init__(
        self,
        name: str,
        server_factory: Callable[[], FastMCP],
        tasks: list[EvalTask] | None = None,
    ) -> None:
        self.name = name
        self.server_factory = server_factory
        self.tasks: list[EvalTask] = tasks or []

    def add(self, task: EvalTask) -> None:
        """Append a task to the suite."""
        self.tasks.append(task)

    async def run(
        self,
        anthropic_client: anthropic.AsyncAnthropic | None = None,
        model: str = "claude-3-5-haiku-20241022",
        pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
    ) -> SuiteReport:
        """Run all tasks and return a :class:`SuiteReport`."""
        server = self.server_factory()
        results: list[EvalResult] = []
        for task in self.tasks:
            result = await run_eval(
                task=task,
                server=server,
                anthropic_client=anthropic_client,
                model=model,
                pass_threshold=pass_threshold,
            )
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        errored = sum(1 for r in results if r.error is not None)
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0
        avg_latency = (
            sum(r.latency_seconds for r in results) / len(results) if results else 0.0
        )

        return SuiteReport(
            suite_name=self.name,
            results=results,
            total=len(results),
            passed=passed,
            failed=len(results) - passed - errored,
            errored=errored,
            avg_score=avg_score,
            avg_latency_seconds=avg_latency,
        )


async def run_suite(
    suite: EvalSuite,
    anthropic_client: anthropic.AsyncAnthropic | None = None,
    model: str = "claude-3-5-haiku-20241022",
    pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
) -> SuiteReport:
    """Convenience wrapper to run a suite (mirrors :meth:`EvalSuite.run`)."""
    return await suite.run(
        anthropic_client=anthropic_client,
        model=model,
        pass_threshold=pass_threshold,
    )
