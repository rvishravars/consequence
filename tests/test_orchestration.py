"""Integration tests for orchestration."""

import pytest
from evaluator.orchestrator import EvalSuite
from evaluator.types import EvalTask
from mcp.server.fastmcp import FastMCP

def test_suite_initialization():
    def make_server():
        return FastMCP("test")

    suite = EvalSuite(
        name="test_suite",
        server_factory=make_server,
        tasks=[
            EvalTask(id="1", description="d", user_message="m")
        ]
    )
    assert suite.name == "test_suite"
    assert len(suite.tasks) == 1

@pytest.mark.asyncio
async def test_registry_discovery():
    from evaluator.registry import get_suite, discover_plugins, list_suites
    # Assuming calculator is in the eval.suites package
    discover_plugins("eval.suites")
    suites = list_suites()
    assert "calculator" in suites
    
    calc = get_suite("calculator")
    assert calc is not None
    assert calc.name == "calculator"
