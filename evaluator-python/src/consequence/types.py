"""Core data types for the consequence eval framework."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    """Records a single tool call made by an agent during a task."""

    name: str
    arguments: dict[str, Any]
    result: Any


class EvalTask(BaseModel):
    """Defines a single evaluation task."""

    id: str
    description: str
    user_message: str
    system_prompt: str = "You are a helpful assistant. Use the available tools to complete tasks."

    # Optional expected values used by built-in evaluators
    expected_output: str | None = None
    expected_tool_names: list[str] = Field(default_factory=list)

    # Custom evaluator: receives (result: EvalResult) -> float score in [0, 1].
    # When None, the default evaluator is used (exact / tool-name matching).
    evaluator: Callable[[EvalResult], float] | None = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}


class EvalResult(BaseModel):
    """The outcome of running a single EvalTask."""

    task_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    output: str | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    error: str | None = None
    latency_seconds: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


class SuiteReport(BaseModel):
    """Aggregated report for an EvalSuite run."""

    suite_name: str
    results: list[EvalResult]
    total: int
    passed: int
    failed: int
    errored: int
    avg_score: float
    avg_latency_seconds: float
