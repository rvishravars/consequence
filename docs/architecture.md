This document visualises the architecture of the **consequence** evaluation toolkit. The system uses a unified control plane (Python Copilot CLI) that orchestrates a specialized Python Evaluation Engine capable of hosting and testing Model Context Protocol (MCP) agents.

## Component Overview

The architecture is divided into a high-level **Control Plane** (Python Copilot CLI) and a low-level **Execution Engine** (Python Evaluation Engine).

```mermaid
flowchart TD
    User([User]) -- "Natural Language / CLI" --> Copilot[Copilot CLI Console]
    
subgraph Layer 1+2: Platform [evaluator]
    PyAPI[FastAPI]
    SSE[SSE Transport]
    Orchestrator[Suite Orchestrator]
    Registry[Suite Registry]
    DB[(jobs_db.json)]
end

subgraph Layer 3: Content [eval]
    subgraph Isolation Layer
        Orchestrator -- "Lookup Runner" --> Registry
        Orchestrator -- "JSON over Stdin" --> AgentProc[Agent Runner Process]
        Orchestrator -- "fork/spawn" --> JudgeProc[Judge Runner Process]
        AgentProc -- "JSON over Stdout" --> Orchestrator
    end
    
    AgentProc -- "MCP Protocol" --> MCP[FastMCP Server]
end

    style Copilot fill:#f9f,stroke:#333,stroke-width:2px
    style PyAPI fill:#ff9,stroke:#333,stroke-width:2px
    style AgentProc fill:#bfb,stroke:#333,stroke-width:2px
    style Orchestrator fill:#bbf,stroke:#333,stroke-width:2px
```

## Evaluation Sequence

The following diagram illustrates the low-level sequence of events when starting an evaluation job from the Copilot CLI.

```mermaid
sequenceDiagram
    participant U as User
    participant J as Copilot CLI
    participant P as Python API
    participant O as Orchestrator
    participant A as Agent Runner
    participant M as FastMCP Server
    participant L as Agent LLM
    participant JD as Judge LLM

    U->>J: "Run the calculator suite"
    J->>P: POST /evaluate/suite/calculator
    activate P
    P->>P: Create Job UUID (jobs_db.json)
    P-->>J: Return Job ID
    deactivate P
    J-->>U: "Job Started: <UUID>"

    Note over P,O: Background Task Begins
    P->>O: run_suite(calculator)
    activate O
    
    loop For each task
        O->>A: Spawn Runner (from Registry)
        O->>A: Send Task JSON (Stdin)
        activate A
        A->>M: Initialize FastMCP instance
        A->>L: /v1/chat/completions (System Prompt + Task)
        
        loop Agent Loop
            L-->>A: Tool Call request
            A->>M: Execute Tool locally
            M-->>A: Tool Result
            A->>L: /v1/chat/completions (Tool Output)
        end
        
        L-->>A: Final Answer
        A-->>O: Send Result JSON (Stdout)
        deactivate A
        
        O->>JD: Spawn subprocess (judge_runner)
        JD->>JD: Score result vs criteria
        JD-->>O: Score (0.0 - 1.0)
    end
    
    O->>P: Save Final SuiteReport to jobs_db.json
    deactivate O
    
    U->>J: eval status --job <UUID>
    J->>P: GET /evaluate/status/<UUID>
    P-->>J: Status: COMPLETED / Results...
    J-->>U: Formatted Evaluation Report
```

## Class Relationships

The following diagram shows the logical relationships between the Python Copilot control plane and the Python execution engine's data models.

```mermaid
classDiagram
    direction LR

    subgraph Python Copilot Control Plane
        class CopilotMain {
            +run_loop()
            +process_nlp_request()
        }
        class APIClient {
            +start_eval()
            +get_status()
            +list_jobs()
        }
        class PydanticModels {
            <<Data>>
            EvalTask
            EvalResult
            SuiteReport
        }
    end

    subgraph Python Execution Engine
        class API {
            <<cli.api>>
            +start_evaluation()
            +get_status()
            +list_jobs()
        }
        class EvalSuite {
            <<evaluator.orchestrator>>
            +name: str
            +server_factory: Callable
            +run()
        }
        class EvalTask {
            <<evaluator.types>>
            +id: str
            +description: str
            +user_message: str
        }
        class Registry {
            <<evaluator.registry>>
            +register_suite()
            +get_suite()
        }
        class Runner {
            <<eval.runners>>
            +agent_runner
            +judge_runner
        }
    end

    CopilotMain ..> APIClient : uses
    APIClient ..> API : HTTP/JSON
    API ..> PydanticModels : mirrors
    
    EvalSuite "1" *-- "*" EvalTask : contains
    EvalSuite ..> SuiteReport : produces
    SuiteReport "1" *-- "*" EvalResult : contains
    EvalTask ..> EvalResult : generates
```

## Design Principles

1.  **Process Isolation**: Every agent task runs in its own isolated Python process. This ensures that the global state of one MCP server doesn't "leak" into another task's evaluation.
2.  **Stateless Control**: The Copilot CLI is completely stateless. It communicates with the Python engine over a REST API, making it easy to swap the CLI for a web UI or CI/CD runner in the future.
3.  **Persistence**: Job statuses are stored in a simple JSON flat-file. This provides persistence across container restarts while remaining lightweight enough to run on single-core CPU environments.
