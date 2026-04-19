"""Integration tests for the evaluation engine using in-process MCP servers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from consequence.eval import EvalSuite, run_eval
from consequence.servers.calculator import make_calculator_server
from consequence.servers.database import make_database_server
from consequence.types import EvalTask


def _make_text_response(text: str):
    """Build a minimal Anthropic Messages response with a text block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_tool_response(tool_name: str, tool_id: str, tool_input: dict, follow_up_text: str):
    """Build a two-step response sequence: tool_use then end_turn."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.id = tool_id
    tool_block.input = tool_input

    first_response = MagicMock()
    first_response.stop_reason = "tool_use"
    first_response.content = [tool_block]

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = follow_up_text

    second_response = MagicMock()
    second_response.stop_reason = "end_turn"
    second_response.content = [text_block]

    return [first_response, second_response]


@pytest.mark.asyncio
async def test_run_eval_no_tool_call():
    """Agent answers directly without calling any tool."""
    mock_client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_messages = AsyncMock()
    mock_client.messages = mock_messages
    mock_messages.create = AsyncMock(return_value=_make_text_response("The answer is 42."))

    task = EvalTask(
        id="test_direct",
        description="direct answer",
        user_message="What is the answer?",
        expected_output="42",
    )

    result = await run_eval(
        task=task,
        server=make_calculator_server(),
        anthropic_client=mock_client,
    )

    assert result.task_id == "test_direct"
    assert result.output == "The answer is 42."
    assert result.error is None
    assert result.score > 0


@pytest.mark.asyncio
async def test_run_eval_with_tool_call():
    """Agent calls the 'add' tool and returns the result."""
    responses = _make_tool_response(
        tool_name="add",
        tool_id="call_1",
        tool_input={"a": 42, "b": 58},
        follow_up_text="The answer is 100.",
    )

    mock_client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_messages = AsyncMock()
    mock_client.messages = mock_messages
    mock_messages.create = AsyncMock(side_effect=responses)

    task = EvalTask(
        id="test_add",
        description="add two numbers",
        user_message="What is 42 + 58?",
        expected_output="100",
        expected_tool_names=["add"],
    )

    result = await run_eval(
        task=task,
        server=make_calculator_server(),
        anthropic_client=mock_client,
    )

    assert result.error is None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "add"
    assert result.score == 1.0
    assert result.passed is True


@pytest.mark.asyncio
async def test_run_eval_agent_exception():
    """Errors during the agent run are captured and scored as 0."""
    mock_client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_messages = AsyncMock()
    mock_client.messages = mock_messages
    mock_messages.create = AsyncMock(side_effect=RuntimeError("API error"))

    task = EvalTask(
        id="test_error",
        description="error task",
        user_message="Fail please.",
    )

    result = await run_eval(
        task=task,
        server=make_calculator_server(),
        anthropic_client=mock_client,
    )

    assert result.error is not None
    assert result.score == 0.0
    assert result.passed is False


@pytest.mark.asyncio
async def test_eval_suite_run():
    """EvalSuite.run returns a SuiteReport with correct counts."""
    responses_t1 = _make_tool_response("add", "c1", {"a": 1, "b": 2}, "3")
    responses_t2 = _make_tool_response("multiply", "c2", {"a": 3, "b": 3}, "9")

    call_count = 0

    async def _side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        # two API calls per task (tool_use + end_turn)
        if call_count in (1, 2):
            return responses_t1[(call_count - 1) % 2]
        return responses_t2[(call_count - 3) % 2]

    mock_client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_messages = AsyncMock()
    mock_client.messages = mock_messages
    mock_messages.create = AsyncMock(side_effect=_side_effect)

    suite = EvalSuite(
        name="test_suite",
        server_factory=make_calculator_server,
        tasks=[
            EvalTask(
                id="t1",
                description="add",
                user_message="1+2",
                expected_tool_names=["add"],
            ),
            EvalTask(
                id="t2",
                description="multiply",
                user_message="3*3",
                expected_tool_names=["multiply"],
            ),
        ],
    )

    report = await suite.run(anthropic_client=mock_client)

    assert report.total == 2
    assert report.suite_name == "test_suite"


@pytest.mark.asyncio
async def test_custom_evaluator():
    """A custom evaluator function is used instead of the default scorer."""
    mock_client = AsyncMock(spec=anthropic.AsyncAnthropic)
    mock_messages = AsyncMock()
    mock_client.messages = mock_messages
    mock_messages.create = AsyncMock(return_value=_make_text_response("hello world"))

    def always_half(result):
        return 0.5

    task = EvalTask(
        id="custom_eval",
        description="custom evaluator test",
        user_message="Say something.",
        evaluator=always_half,
    )

    result = await run_eval(
        task=task,
        server=make_calculator_server(),
        anthropic_client=mock_client,
    )

    assert result.score == 0.5


@pytest.mark.asyncio
async def test_database_server_tools_exposed():
    """Database server exposes the expected tools over MCP."""
    from mcp.shared.memory import create_connected_server_and_client_session

    server = make_database_server()
    async with create_connected_server_and_client_session(server) as session:
        tools_result = await session.list_tools()
        tool_names = {t.name for t in tools_result.tools}

    assert "get_product" in tool_names
    assert "check_stock" in tool_names
    assert "search_products" in tool_names
    assert "get_employee" in tool_names
    assert "list_employees_by_department" in tool_names


@pytest.mark.asyncio
async def test_calculator_server_tools_exposed():
    """Calculator server exposes the expected tools over MCP."""
    from mcp.shared.memory import create_connected_server_and_client_session

    server = make_calculator_server()
    async with create_connected_server_and_client_session(server) as session:
        tools_result = await session.list_tools()
        tool_names = {t.name for t in tools_result.tools}

    assert "add" in tool_names
    assert "subtract" in tool_names
    assert "multiply" in tool_names
    assert "divide" in tool_names
    assert "power" in tool_names


@pytest.mark.asyncio
async def test_calculator_tool_add():
    """Calling the add tool via MCP returns the correct result."""
    from mcp.shared.memory import create_connected_server_and_client_session

    server = make_calculator_server()
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("add", {"a": 7, "b": 3})
        content = result.content[0].text
    assert "10" in content


@pytest.mark.asyncio
async def test_database_tool_get_product():
    """Calling get_product returns product info."""
    from mcp.shared.memory import create_connected_server_and_client_session

    server = make_database_server()
    async with create_connected_server_and_client_session(server) as session:
        result = await session.call_tool("get_product", {"product_id": "P001"})
        content = result.content[0].text
    assert "Widget A" in content
