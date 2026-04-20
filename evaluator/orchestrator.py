"""Evaluation engine: runs tasks against MCP-backed agents."""

from __future__ import annotations

import time
from typing import Any, Callable, Coroutine

import anyio
from openai import AsyncOpenAI
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session


from evaluator.metrics import combined_score
from eval.llm_evaluator import make_llm_judge
from evaluator.types import EvalResult, EvalTask, SuiteReport
from evaluator.registry import get_agent_runner, discover_plugins

_DEFAULT_PASS_THRESHOLD = 0.5


async def run_eval(
    task: EvalTask,
    server: FastMCP,
    model: str = "gemma4",
    pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
    llm_judge: bool = False,
    suite_name: str = "calculator",
    agent_name: str = "default",
) -> EvalResult:
    """Run a single :class:`EvalTask` via isolated subprocesses."""
    import json
    import sys
    from asyncio.subprocess import PIPE
    from evaluator.metrics import combined_score
    
    start = time.monotonic()
    
    # 1. Lookup Agent Runner
    # Ensure runners are discovered if not already
    discover_plugins("eval.runners")
    runner_factory = get_agent_runner(agent_name)
    if not runner_factory:
        return EvalResult(
            task_id=task.id,
            passed=False,
            score=0.0,
            error=f"Agent '{agent_name}' not found in registry.",
            latency_seconds=time.monotonic() - start,
        )

    agent_cmd = runner_factory(task=task, model=model, suite_name=suite_name)
    
    # 2. Run Agent Process with JSON-over-Stdin/Stdout protocol
    input_data = {
        "task": task.model_dump(),
        "model": model,
        "suite_name": suite_name,
    }
    
    import anyio.abc
    try:
        # We use anyio.run_process for simple cases, but for STDIN we need more control
        # Actually anyio.run_process supports input= argument
        proc = await anyio.run_process(
            agent_cmd, 
            input=json.dumps(input_data).encode("utf-8"),
            check=False
        )
        stdout_str = proc.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return EvalResult(
            task_id=task.id,
            passed=False,
            score=0.0,
            error=f"Failed to spawn agent process: {e}",
            latency_seconds=time.monotonic() - start,
        )

    # Need to extract the last valid JSON output line
    result_dict = {}
    for line in stdout_str.splitlines()[::-1]:
        try:
            result_dict = json.loads(line)
            break
        except Exception:
            continue
            
    if not result_dict:
        return EvalResult(
            task_id=task.id,
            passed=False,
            score=0.0,
            error=f"Agent subprocess failed to return valid JSON. Output: {stdout_str[-200:]}",
            latency_seconds=time.monotonic() - start,
        )
        
    result = EvalResult(**result_dict)
    
    # 3. Run Judge Process
    if task.evaluator is not None:
        score = task.evaluator(result)
    elif llm_judge:
        judge_cmd = [
            sys.executable,
            "-m", "eval.runners.judge_runner",
            "--suite", suite_name,
            "--task-id", task.id,
            "--result", json.dumps(result_dict),
        ]
        judge_proc = await anyio.run_process(judge_cmd, check=False)
        stdout_str = judge_proc.stdout.decode("utf-8", errors="replace")
        score = 0.0
        for line in stdout_str.splitlines()[::-1]:
            try:
                judge_res = json.loads(line)
                score = judge_res.get("score", 0.0)
                break
            except Exception:
                continue
    else:
        score = combined_score(result, task)

    result.score = max(0.0, min(1.0, score))
    result.passed = result.score >= pass_threshold
    # Ensure latency represents the total time
    result.latency_seconds = time.monotonic() - start
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
        model: str = "gemma4",
        pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
        llm_judge: bool = False,
        agent_name: str = "default",
    ) -> SuiteReport:
        """Run all tasks and return a :class:`SuiteReport`."""
        # server is not needed for run_eval anymore since isolated, but we keep it for backward compat or just not pass it if not used. 
        # Actually run_eval still expects `server` arg because we didn't remove it from signature, but it's ignored inside.
        server = self.server_factory()
        results: list[EvalResult] = []
        for task in self.tasks:
            result = await run_eval(
                task=task,
                server=server,
                model=model,
                pass_threshold=pass_threshold,
                llm_judge=llm_judge,
                suite_name=self.name,
                agent_name=agent_name,
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
    model: str = "gemma4",
    pass_threshold: float = _DEFAULT_PASS_THRESHOLD,
    llm_judge: bool = False,
    agent_name: str = "default",
) -> SuiteReport:
    """Convenience wrapper to run a suite (mirrors :meth:`EvalSuite.run`)."""
    return await suite.run(
        model=model,
        pass_threshold=pass_threshold,
        llm_judge=llm_judge,
        agent_name=agent_name,
    )
