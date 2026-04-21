A Python-native agent evaluation toolkit using a monorepo structure. Ensure you run `sudo docker compose build` from the root directory to build the tools before using them.

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

### 3-Tier Architecture

The engine is divided into three distinct layers to ensure separation of concerns and maintainability:

#### 1+2. Platform Layer (`evaluator/`)
- **API (`evaluator.api`)**: A FastAPI-based REST interface that orchestrates evaluation jobs.
- **CLI (`evaluator.main`)**: The command-line interface for running evaluations locally.
- **Orchestrator**: The core logic that manages evaluation lifecycles, spawns isolated subprocesses, and aggregates results.
- **Registry**: A dynamic discovery system for registering and retrieving evaluation suites and agent implementations.
- **Metrics**: Standard scoring functions (exact match, contains, numeric, etc.).
- **Persistence**: Manages results in `jobs_db.json`.

#### 3. Content Layer (`eval/`)
- **Suites**: Definitions of evaluation tasks and their expected outcomes.
- **Servers**: Contains the implementation of mock MCP servers (e.g., `calculator`) used for testing.
- **Agent Loop**: The logic for running an LLM agent against an MCP server.
- **Runners**: Isolated entry points (`agent_runner`, `judge_runner`) for process-level safety.

### Prerequisites

Before running the evaluation framework, ensure your system has the following installed and configured:

1. **Docker & Docker Compose**: The entire project executes within containerized environments.
2. **Ollama**: A local LLM runner must be active (usually at `http://localhost:11434`).
3. **Local Models**: You must pull the models you intend to use for evaluation and judging.
   ```bash
   ollama pull llama3.2:1b
   ollama pull gemma4
   ```

The recommended way to run `consequence` is via **Docker Compose**, which ensures all dependencies and Python runtimes are correctly isolated and configured.

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
Once the REPL loads, try asking it to run evaluations, check job statuses, or manage your history:

> *"Run the calculator suite using the default agent."*
> *"List all my active or past evaluation jobs."*
> *"Get the complete report for job [UUID]."*
> *"Delete all my job history, please."*

The Copilot will interpret your request, trigger the isolated evaluation in the backend, and optionally present the formatted JSON results directly in your terminal when they finish!

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

### Defining an Evaluation Suite

Suites are defined in `eval/suites/`. A suite consists of a server factory and a list of `EvalTask` objects. Use `register_suite` to make them discoverable.

```python
from evaluator.orchestrator import EvalSuite
from evaluator.types import EvalTask
from evaluator.registry import register_suite
from eval.servers.calculator import make_calculator_server

calculator_suite = register_suite(EvalSuite(
    name="calculator",
    server_factory=make_calculator_server,
    tasks=[
        EvalTask(
            id="task_1",
            user_message="What is 5 + 5?",
            expected_output="10",
        ),
    ],
))
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

- [Architecture Guide](docs/architecture.md): Visual diagrams and technical overview of the system.

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

### Persistence

Evaluation results are stored in `jobs_db.json` at the root of the project. Each entry contains the job status, a full report of each task, and any errors encountered during the run.

---

### Python Local Development

```bash
# Install dependencies from the root
pip install -e ".[dev]"
pytest

# Run evaluations directly via Python CLI
consequence --suite calculator --model llama3.2:1b
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
