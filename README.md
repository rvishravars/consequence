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

### Getting Started

The recommended way to run `consequence` is via **Docker Compose**, which ensures all language runtimes (Java, Python) and dependencies are correctly isolated and configured.

To build the environment:
```bash
sudo docker compose build
```

### Quick Start

The easiest way to test the sample agent (which uses the `calculator` tool) is via Docker Compose and the new interactive Copilot CLI.

**1. Start the Evaluation Engine in the background:**
```bash
sudo docker compose up -d python-eval-backend
```

**2. Launch the interactive Copilot CLI:**
```bash
sudo docker compose run --rm -it copilot-cli
```

**3. Run the evaluation by talking to the Copilot:**
Once the REPL loads, just type:
> *"Run the calculator suite using the default agent."*

The Copilot will parse your request, trigger the isolated evaluation in the backend, and present the results when they finish!

#### Use the Python API

```python
import asyncio
from openai import AsyncOpenAI
from mcp.server.fastmcp import FastMCP
from evaluator.orchestrator import EvalSuite, run_suite
from evaluator.types import EvalTask

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
from evaluator.types import EvalResult, EvalTask

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

```python
from eval.servers import make_calculator_server
```

### Built-in Eval Suites

```python
# Built-in suites are registered in the eval.suites package
from evaluator.registry import get_suite, discover_plugins
discover_plugins("eval.suites")
calculator_suite = get_suite("calculator")
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
# Use the LLM judge via the Copilot CLI
# In the REPL: "Run the calculator suite using the LLM judge"
```

### Documentation

Detailed documentation for the project is available in the `docs/` directory:

- [Architecture Guide](docs/architecture.md): Visual diagrams and technical overview of the system.
- [Python Evaluator Guide](docs/python-evaluator.md): Deep dive into the Python-side execution engine, core modules, and metric definitions.

### Python Project Structure

```
consequence/
├── evaluator/     # [L1+L2: PLATFORM] API, CLI, Orchestrator, Metrics
├── eval/          # [L3: CONTENT] Suites, Servers, Agent Loop, Runners
├── copilot_cli/   # Interactive AI Copilot Control Plane
├── docs/          # Technical documentation
├── scripts/       # Automation and demo scripts
├── tests/         # Unit and integration tests
├── pyproject.toml # Project configuration
├── Dockerfile     # Docker build context
└── docker-compose.yml
```

### Quick Start (CPU Demo)

To verify the entire 3-tier architecture is functional on a memory-constrained (CPU) environment:

```bash
./scripts/run_cpu_demo.sh
```

---

### Python Local Development

```bash
# Install dependencies from the root
pip install -e ".[dev]"
pytest
```

---

## Interactive Copilot Console

The Pyhton-based Copilot CLI acts as a unified control plane. It does not perform evaluations itself; instead, it orchestrates the **Python Evaluation Engine** via natural language.

### Quick Start via Docker Compose

```bash
# 1. Ensure the backend is running
sudo docker compose up -d python-eval-backend

# 2. Start the copilot loop
sudo docker compose run --rm -it copilot-cli
```

### Configuration

Environment variables (passed to the copilot-cli service):

| Environment variable       | Default                          | Description                              |
|---------------------------|----------------------------------|------------------------------------------|
| `PYTHON_EVAL_URL`         | `http://python-eval-backend:8000`| Python API endpoint                       |
| `AGENT_MODEL`             | `gemma4`                         | Model name for the Copilot & Agent         |
