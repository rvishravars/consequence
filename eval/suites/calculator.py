"""Evaluation suite for the built-in calculator MCP server."""

from __future__ import annotations

from evaluator.orchestrator import EvalSuite
from eval.servers.calculator import make_calculator_server
from evaluator.types import EvalTask

from evaluator.registry import register_suite

calculator_suite = register_suite(EvalSuite(
    name="calculator",
    server_factory=make_calculator_server,
    tasks=[
        EvalTask(
            id="calc_add_integers",
            description="Agent adds two integers using the add tool",
            user_message="What is 42 + 58?",
            expected_output="100",
            expected_tool_names=["add"],
        ),
    ],
))
