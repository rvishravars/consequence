"""Unit tests for evaluation metrics."""

import pytest
from evaluator.metrics import (
    exact_match,
    contains_match,
    numeric_match,
    tool_name_match,
    combined_score
)
from evaluator.types import EvalResult, ToolCallRecord

from evaluator.types import EvalResult, ToolCallRecord, EvalTask

def test_exact_match():
    res = EvalResult(task_id="t1", passed=False, score=0.0, output="  Hello World  ")
    task = EvalTask(id="t1", description="d", user_message="m", expected_output="Hello World")
    assert exact_match(res, task) == 1.0
    
    task_wrong = EvalTask(id="t1", description="d", user_message="m", expected_output="Wrong")
    assert exact_match(res, task_wrong) == 0.0

def test_contains_match():
    res = EvalResult(task_id="t1", passed=False, score=0.0, output="The answer is 42.")
    task = EvalTask(id="t1", description="d", user_message="m", expected_output="42")
    assert contains_match(res, task) == 1.0
    
    task_missing = EvalTask(id="t1", description="d", user_message="m", expected_output="missing")
    assert contains_match(res, task_missing) == 0.0

def test_numeric_match():
    res = EvalResult(task_id="t1", passed=False, score=0.0, output="It costs $123.45 total.")
    task = EvalTask(id="t1", description="d", user_message="m", expected_output="123.45")
    assert numeric_match(res, task) == 1.0
    
    task_wrong = EvalTask(id="t1", description="d", user_message="m", expected_output="100")
    assert numeric_match(res, task_wrong) == 0.0

def test_tool_name_match():
    res = EvalResult(
        task_id="t1",
        passed=False,
        score=0.0,
        tool_calls=[
            ToolCallRecord(name="add", arguments={}, result=""),
            ToolCallRecord(name="multiply", arguments={}, result="")
        ]
    )
    task = EvalTask(id="t1", description="d", user_message="m", expected_tool_names=["add", "multiply", "subtract"])
    # 2 out of 3 match
    assert tool_name_match(res, task) == pytest.approx(0.66, abs=0.01)
    
    task_exact = EvalTask(id="t1", description="d", user_message="m", expected_tool_names=["add"])
    assert tool_name_match(res, task_exact) == 1.0
