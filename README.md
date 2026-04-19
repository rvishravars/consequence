# consequence

An **MCP-backed agent evaluation framework** for testing LLM agents that use the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

## Overview

`consequence` lets you define evaluation tasks, run an Anthropic Claude agent against a live MCP server, and score the results — all in a few lines of Python.

```
EvalTask → EvalSuite → run_suite() → SuiteReport
                ↓
         FastMCP Server (in-process)
                ↓
         Anthropic Claude Agent
                ↓
         Scoring (metrics)
```

## Installation

```bash
pip install consequence
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Quick Start

### Run built-in suites via CLI

```bash
# Run all built-in eval suites
consequence

# Run only the calculator suite
consequence --suite calculator

# Use a different model
consequence --suite database --model claude-3-5-sonnet-20241022
```

### Use the Python API

```python
import asyncio
import anthropic
from mcp.server.fastmcp import FastMCP
from consequence import EvalTask, EvalSuite, run_suite

# 1. Define a FastMCP server with your tools
def make_server() -> FastMCP:
    mcp = FastMCP("my_server")

    @mcp.tool()
    def greet(name: str) -> str:
        """Return a greeting for the given name."""
        return f"Hello, {name}!"

    return mcp

# 2. Define tasks
suite = EvalSuite(
    name="greetings",
    server_factory=make_server,
    tasks=[
        EvalTask(
            id="greet_alice",
            description="Agent greets Alice using the greet tool",
            user_message="Please greet Alice.",
            expected_output="Hello, Alice!",
            expected_tool_names=["greet"],
        ),
    ],
)

# 3. Run evals
async def main():
    client = anthropic.AsyncAnthropic()
    report = await run_suite(suite, anthropic_client=client)
    print(f"Passed: {report.passed}/{report.total}, avg score: {report.avg_score:.2f}")

asyncio.run(main())
```

### Custom evaluators

```python
from consequence.types import EvalResult, EvalTask

def my_evaluator(result: EvalResult) -> float:
    if result.error:
        return 0.0
    # Score 1.0 if the output mentions "Hello"
    return 1.0 if result.output and "Hello" in result.output else 0.0

task = EvalTask(
    id="custom",
    description="Custom eval",
    user_message="Say hello.",
    evaluator=my_evaluator,
)
```

## Built-in Servers

| Server | Tools |
|--------|-------|
| `calculator` | `add`, `subtract`, `multiply`, `divide`, `power` |
| `database` | `get_product`, `search_products`, `check_stock`, `get_employee`, `list_employees_by_department` |

```python
from consequence.servers import make_calculator_server, make_database_server
```

## Built-in Eval Suites

```python
from consequence.evals import calculator_suite, database_suite
```

## Scoring Metrics

| Metric | Description |
|--------|-------------|
| `exact_match` | 1.0 if output equals expected (stripped) |
| `contains_match` | 1.0 if expected is a substring of the output |
| `numeric_match` | 1.0 if output contains the expected number |
| `tool_name_match` | Fraction of expected tools that were called |
| `combined_score` | Default composite (tool + output score) |

## Project Structure

```
src/consequence/
├── __init__.py        # Public API
├── agent.py           # MCP-backed LLM agentic loop
├── eval.py            # Evaluation orchestration (EvalSuite, run_eval)
├── metrics.py         # Scoring functions
├── reporter.py        # Rich-formatted output
├── cli.py             # CLI entry point
├── types.py           # EvalTask, EvalResult, SuiteReport
└── servers/
    ├── calculator.py  # Built-in calculator MCP server
    └── database.py    # Built-in mock database MCP server
src/consequence/evals/
├── calculator.py      # Built-in calculator eval suite
└── database.py        # Built-in database eval suite
tests/
├── test_eval.py       # Integration tests
└── test_metrics.py    # Unit tests for scoring metrics
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
