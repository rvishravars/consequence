"""Scoring metrics for agent evaluation."""

from __future__ import annotations

import re

from evaluator.types import EvalResult, EvalTask


def exact_match(result: EvalResult, task: EvalTask) -> float:
    """Return 1.0 if the agent output exactly matches the expected output."""
    if task.expected_output is None or result.output is None:
        return 0.0
    return 1.0 if result.output.strip() == task.expected_output.strip() else 0.0


def contains_match(result: EvalResult, task: EvalTask) -> float:
    """Return 1.0 if the expected output is contained in the agent output."""
    if task.expected_output is None or result.output is None:
        return 0.0
    return 1.0 if task.expected_output.strip() in result.output else 0.0


def numeric_match(result: EvalResult, task: EvalTask, tolerance: float = 1e-6) -> float:
    """Return 1.0 when both output and expected contain the same number (within tolerance)."""
    if task.expected_output is None or result.output is None:
        return 0.0

    def _extract(text: str) -> float | None:
        matches = re.findall(r"-?\d+(?:\.\d+)?", text)
        return float(matches[-1]) if matches else None

    expected_num = _extract(task.expected_output)
    actual_num = _extract(result.output)
    if expected_num is None or actual_num is None:
        return 0.0
    return 1.0 if abs(expected_num - actual_num) <= tolerance else 0.0


def tool_name_match(result: EvalResult, task: EvalTask) -> float:
    """Score based on whether the expected tool names were called.

    Returns the fraction of expected tools that were actually called.
    """
    if not task.expected_tool_names:
        return 1.0
    called_names = {tc.name for tc in result.tool_calls}
    matched = sum(1 for name in task.expected_tool_names if name in called_names)
    return matched / len(task.expected_tool_names)


def combined_score(result: EvalResult, task: EvalTask) -> float:
    """Default composite scorer used when no custom evaluator is provided.

    - If ``expected_output`` is set, numeric_match is tried first, then
      contains_match (each weighted 0.5 against tool_name_match).
    - If only ``expected_tool_names`` are set, tool_name_match is returned.
    - If neither is set, defaults to 1.0 (pass by running without error).
    """
    if result.error:
        return 0.0

    has_output = task.expected_output is not None
    has_tools = bool(task.expected_tool_names)

    if not has_output and not has_tools:
        return 1.0

    scores: list[float] = []
    if has_tools:
        scores.append(tool_name_match(result, task))
    if has_output:
        output_score = max(numeric_match(result, task), contains_match(result, task))
        scores.append(output_score)

    return sum(scores) / len(scores)
