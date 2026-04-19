"""Tests for scoring metrics."""

from __future__ import annotations

import pytest

from consequence.metrics import (
    combined_score,
    contains_match,
    exact_match,
    numeric_match,
    tool_name_match,
)
from consequence.types import EvalResult, EvalTask, ToolCallRecord


def _task(**kwargs) -> EvalTask:
    defaults = dict(id="t", description="test", user_message="hello")
    defaults.update(kwargs)
    return EvalTask(**defaults)


def _result(**kwargs) -> EvalResult:
    defaults = dict(task_id="t", passed=True, score=1.0)
    defaults.update(kwargs)
    return EvalResult(**defaults)


class TestExactMatch:
    def test_match(self):
        task = _task(expected_output="42")
        result = _result(output="42")
        assert exact_match(result, task) == 1.0

    def test_mismatch(self):
        task = _task(expected_output="42")
        result = _result(output="43")
        assert exact_match(result, task) == 0.0

    def test_strips_whitespace(self):
        task = _task(expected_output="  42  ")
        result = _result(output="42")
        assert exact_match(result, task) == 1.0

    def test_no_expected(self):
        task = _task()
        result = _result(output="anything")
        assert exact_match(result, task) == 0.0


class TestContainsMatch:
    def test_contained(self):
        task = _task(expected_output="Widget A")
        result = _result(output="The product is Widget A and costs $9.99.")
        assert contains_match(result, task) == 1.0

    def test_not_contained(self):
        task = _task(expected_output="Widget A")
        result = _result(output="Product not found.")
        assert contains_match(result, task) == 0.0


class TestNumericMatch:
    def test_same_number(self):
        task = _task(expected_output="100")
        result = _result(output="The answer is 100.")
        assert numeric_match(result, task) == 1.0

    def test_different_number(self):
        task = _task(expected_output="100")
        result = _result(output="The answer is 99.")
        assert numeric_match(result, task) == 0.0

    def test_no_number_in_output(self):
        task = _task(expected_output="100")
        result = _result(output="I don't know.")
        assert numeric_match(result, task) == 0.0

    def test_float(self):
        task = _task(expected_output="24.99")
        result = _result(output="The price is 24.99 dollars.")
        assert numeric_match(result, task) == 1.0


class TestToolNameMatch:
    def test_all_called(self):
        task = _task(expected_tool_names=["add", "multiply"])
        result = _result(
            tool_calls=[
                ToolCallRecord(name="add", arguments={}, result=3),
                ToolCallRecord(name="multiply", arguments={}, result=6),
            ]
        )
        assert tool_name_match(result, task) == 1.0

    def test_partial(self):
        task = _task(expected_tool_names=["add", "multiply"])
        result = _result(
            tool_calls=[ToolCallRecord(name="add", arguments={}, result=3)]
        )
        assert tool_name_match(result, task) == 0.5

    def test_none_called(self):
        task = _task(expected_tool_names=["add"])
        result = _result(tool_calls=[])
        assert tool_name_match(result, task) == 0.0

    def test_no_expected(self):
        task = _task()
        result = _result(tool_calls=[])
        assert tool_name_match(result, task) == 1.0


class TestCombinedScore:
    def test_error_always_zero(self):
        task = _task(expected_output="42", expected_tool_names=["add"])
        result = _result(error="Some error", score=0.0, passed=False)
        assert combined_score(result, task) == 0.0

    def test_no_expectations_returns_one(self):
        task = _task()
        result = _result(output="anything")
        assert combined_score(result, task) == 1.0

    def test_only_tools(self):
        task = _task(expected_tool_names=["add"])
        result = _result(
            tool_calls=[ToolCallRecord(name="add", arguments={}, result=5)]
        )
        assert combined_score(result, task) == 1.0

    def test_tools_and_output(self):
        task = _task(expected_output="100", expected_tool_names=["add"])
        result = _result(
            output="The answer is 100.",
            tool_calls=[ToolCallRecord(name="add", arguments={}, result=100)],
        )
        assert combined_score(result, task) == 1.0
