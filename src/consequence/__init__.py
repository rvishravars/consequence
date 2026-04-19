"""Consequence: MCP-backed agent evaluation framework."""

from consequence.eval import EvalSuite, run_eval, run_suite
from consequence.types import EvalResult, EvalTask, ToolCallRecord

__all__ = [
    "EvalTask",
    "EvalResult",
    "EvalSuite",
    "ToolCallRecord",
    "run_eval",
    "run_suite",
]
