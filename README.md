# consequence

A multi-language agent evaluation toolkit using a monorepo structure. Ensure you run `sudo docker compose build` from the root directory to build the tools before using them.

---

## Python: MCP-backed Agent Eval

An **MCP-backed agent evaluation framework** for testing LLM agents that use the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

### Overview

`consequence` lets you define evaluation tasks, run a local agent (like **Gemma 4**) against a live MCP server, and score the results — all in a few lines of Python.

```
EvalTask → EvalSuite → run_suite() → SuiteReport
                ↓
         FastMCP Server (in-process)
                ↓
         Local Agent (Gemma 4 / Ollama)
                ↓
         Scoring (metrics)
```

### Installation

```bash
pip install consequence
```

Set your model configuration (defaults to Ollama):

```bash
export AGENT_BASE_URL=http://localhost:11434/v1
export AGENT_MODEL=gemma4
```

### Quick Start

#### Run built-in suites via Docker Compose

```bash
# Run all built-in eval suites
sudo docker compose run --rm python-eval

# Run only the calculator suite
sudo docker compose run --rm python-eval --suite calculator

# Use a different model
sudo docker compose run --rm python-eval --suite database --model gemma4:9b
```

#### Use the Python API

```python
import asyncio
from openai import AsyncOpenAI
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
    client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    report = await run_suite(suite, client=client, model="gemma4")
    print(f"Passed: {report.passed}/{report.total}, avg score: {report.avg_score:.2f}")

asyncio.run(main())
```

#### Custom evaluators

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

### Built-in Servers

| Server | Tools |
|--------|-------|
| `calculator` | `add`, `subtract`, `multiply`, `divide`, `power` |
| `database` | `get_product`, `search_products`, `check_stock`, `get_employee`, `list_employees_by_department` |

```python
from consequence.servers import make_calculator_server, make_database_server
```

### Built-in Eval Suites

```python
from consequence.evals import calculator_suite, database_suite
```

### Scoring Metrics

| Metric | Description |
|--------|-------------|
| `exact_match` | 1.0 if output equals expected (stripped) |
| `contains_match` | 1.0 if expected is a substring of the output |
| `numeric_match` | 1.0 if output contains the expected number |
| `tool_name_match` | Fraction of expected tools that were called |
| `combined_score` | Default composite (tool + output score) |

### LLM-as-a-Judge

You can use a separate LLM (the "Judge") to evaluate the agent's performance. This is useful for complex tasks where simple string matching isn't enough.

#### Configuration

Set the following environment variables to configure the judge:

```bash
export JUDGE_MODEL=llama3.2        # The model that will score the results
export JUDGE_BASE_URL=http://...   # Endpoint for the judge model
export JUDGE_API_KEY=...           # optional
```

#### Usage

Run the CLI with the `--llm-judge` flag:

```bash
sudo docker compose run --rm python-eval --llm-judge
```

### Python Project Structure

```
evaluator-python/
├── src/consequence/
│   ├── __init__.py        # Public API
│   ├── agent.py           # MCP-backed LLM agentic loop
│   ├── eval.py            # Evaluation orchestration (EvalSuite, run_eval)
│   ├── metrics.py         # Scoring functions
│   ├── reporter.py        # Rich-formatted output
│   ├── cli.py             # CLI entry point
│   ├── types.py           # EvalTask, EvalResult, SuiteReport
│   ├── servers/
│   │   ├── calculator.py  # Built-in calculator MCP server
│   │   └── database.py    # Built-in mock database MCP server
│   └── evals/
│       ├── calculator.py  # Built-in calculator eval suite
│       └── database.py    # Built-in database eval suite
├── tests/
│   ├── test_eval.py       # Integration tests
│   └── test_metrics.py    # Unit tests for scoring metrics
└── pyproject.toml
```

### Python Local Development

```bash
cd evaluator-python/
pip install -e ".[dev]"
pytest
```

---

## Java: Agent Eval CLI

Agent evaluation tool – a CLI built with **Java 25**, **Spring Shell**, and **Maven**.

Point it at any [OpenAI-compatible](https://platform.openai.com/docs/api-reference/chat) chat-completions endpoint (e.g. Ollama, OpenAI, vLLM) and run structured evaluation suites to measure agent quality.

### Requirements

| Tool | Version |
|------|---------|
| JDK  | 25+     |
| Maven | 3.8+   |
| Docker| 20+    |

### Quick Start via Docker Compose

```bash
# Get help and commands
sudo docker compose run --rm java-cli help

# List eval cases from sample-eval.json at the repo root
sudo docker compose run --rm java-cli eval list --suite sample-eval.json

# Run the eval suite
sudo docker compose run --rm java-cli eval run --suite sample-eval.json

# Run and print detailed report
sudo docker compose run --rm java-cli eval report --suite sample-eval.json
```

### Local Development (Without Docker)

Navigate specifically to the Java directory:
```bash
cd cli-java/
mvn clean package -q
java -jar target/consequence-0.1.0-SNAPSHOT.jar eval run --suite ../sample-eval.json
```

### Configuration

Configuration is read from `cli-java/src/main/resources/application.yml` or from environment variables:

| Environment variable       | Default                          | Description                              |
|---------------------------|----------------------------------|------------------------------------------|
| `AGENT_BASE_URL`          | `http://localhost:11434/v1`      | Base URL of the chat-completions endpoint |
| `AGENT_API_KEY`           | *(empty)*                        | Bearer token / API key (optional)         |
| `AGENT_MODEL`             | `llama3`                         | Model name sent in the request body       |
| `AGENT_TIMEOUT_SECONDS`   | `60`                             | HTTP call timeout                         |

An eval suite is a JSON array of evaluation cases:

```json
[
  {
    "id": "c1",
    "description": "Greeting check",
    "input": "Say hello in one word.",
    "expectedOutput": "hello",
    "scoringMethod": "CONTAINS"
  },
  {
    "id": "c2",
    "description": "Exact capital city",
    "input": "What is the capital of France? One word.",
    "expectedOutput": "Paris",
    "scoringMethod": "EXACT"
  },
  {
    "id": "c3",
    "description": "Phone number regex",
    "input": "Give me a US phone number example.",
    "expectedPattern": "\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}",
    "scoringMethod": "REGEX"
  },
  {
    "id": "c4",
    "description": "Free-form (always passes)",
    "input": "Tell me a fun fact.",
    "scoringMethod": "NONE"
  }
]
```

### Scoring methods

| Method     | Description |
|------------|-------------|
| `CONTAINS` | Pass if the agent response contains `expectedOutput` (case-insensitive) |
| `EXACT`    | Pass if the agent response equals `expectedOutput` after trimming (case-insensitive) |
| `REGEX`    | Pass if the agent response matches `expectedPattern` |
| `NONE`     | Always pass – useful for manual review or latency-only benchmarks |

### Run tests

```bash
mvn test
```
