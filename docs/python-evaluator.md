# Python Evaluation Engine

The Python-side of **consequence** is a high-performance evaluation engine designed to test AI agents using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It is organized into a modular 3-tier monolithic structure.

## 3-Tier Architecture

The engine is divided into three distinct layers to ensure separation of concerns and maintainability:

### 1+2. Platform Layer (`evaluator/`)
- **API (`evaluator.api`)**: A FastAPI-based REST interface that orchestrates evaluation jobs.
- **CLI (`evaluator.main`)**: The command-line interface for running evaluations locally.
- **Orchestrator**: The core logic that manages evaluation lifecycles, spawns isolated subprocesses, and aggregates results.
- **Registry**: A dynamic discovery system for registering and retrieving evaluation suites and agent implementations.
- **Metrics**: Standard scoring functions (exact match, contains, numeric, etc.).
- **Persistence**: Manages results in `jobs_db.json`.

### 3. Content Layer (`eval/`)
- **Suites**: Definitions of evaluation tasks and their expected outcomes.
- **Servers**: Contains the implementation of mock MCP servers (e.g., `calculator`) used for testing.
- **Agent Loop**: The logic for running an LLM agent against an MCP server.
- **Runners**: Isolated entry points (`agent_runner`, `judge_runner`) for process-level safety.

---

## Getting Started

### Installation
From the repository root, install the package in editable mode:
```bash
pip install -e "."
```

### Configuration
The engine relies on environment variables for model targeting:
```bash
export AGENT_MODEL=llama3.2:1b
export AGENT_BASE_URL=http://localhost:11434/v1
export JUDGE_MODEL=llama3.2:1b
export JUDGE_BASE_URL=http://localhost:11434/v1
```

---

## Defining an Evaluation Suite

Suites are defined in `eval/suites/`. A suite consists of a server factory and a list of `EvalTask` objects.

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

---

## Running Evaluations

### Via Java CLI (Recommended)
The Java CLI provides the unified command interface:
```bash
./scripts/run_cpu_demo.sh
```

### Via Python CLI
You can also run evaluations directly using the Python entry point:
```bash
consequence --suite calculator --model llama3.2:1b
```

---

## Persistence
Evaluation results are stored in `jobs_db.json` at the root of the project. Each entry contains the job status, a full report of each task, and any errors encountered during the run.
