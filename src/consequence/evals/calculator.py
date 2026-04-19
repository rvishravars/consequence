"""Evaluation suite for the built-in calculator MCP server."""

from __future__ import annotations

from consequence.eval import EvalSuite
from consequence.servers.calculator import make_calculator_server
from consequence.types import EvalTask

calculator_suite = EvalSuite(
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
        EvalTask(
            id="calc_subtract",
            description="Agent subtracts two numbers",
            user_message="What is 200 minus 75?",
            expected_output="125",
            expected_tool_names=["subtract"],
        ),
        EvalTask(
            id="calc_multiply",
            description="Agent multiplies two numbers",
            user_message="Multiply 12 by 15.",
            expected_output="180",
            expected_tool_names=["multiply"],
        ),
        EvalTask(
            id="calc_divide",
            description="Agent divides two numbers",
            user_message="Divide 144 by 12.",
            expected_output="12",
            expected_tool_names=["divide"],
        ),
        EvalTask(
            id="calc_power",
            description="Agent raises a number to a power",
            user_message="What is 2 raised to the power of 10?",
            expected_output="1024",
            expected_tool_names=["power"],
        ),
        EvalTask(
            id="calc_chained",
            description="Agent chains multiple arithmetic operations",
            user_message="Calculate (5 + 3) * 7.",
            expected_output="56",
            expected_tool_names=["add", "multiply"],
        ),
        EvalTask(
            id="calc_divide_by_zero",
            description="Agent handles division by zero gracefully",
            user_message="What is 10 divided by 0?",
            expected_tool_names=["divide"],
        ),
    ],
)
