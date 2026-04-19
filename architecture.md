# Consequence Architecture

This document visualises the architecture of the **consequence** evaluation toolkit, which consists of two distinct components: the Python MCP-backed evaluator and the Java CLI evaluator.

## Python: MCP-Backed Agent Evaluation

The Python component is designed to evaluate Anthropic Claude agents interacting with Model Context Protocol (MCP) servers. It orchestrates the entire flow from defining tasks to interacting with the agent and scoring the final output.

```mermaid
flowchart TD
    subgraph Definition
        Task1[EvalTask] --> Suite[EvalSuite]
        Task2[EvalTask] --> Suite
    end

    Suite --> Runner[run_suite]
    
    subgraph Execution Loop
        Runner -- "Hosts" --> MCP["FastMCP Server<br/>(in-process)"]
        Runner -- "Prompts" --> Agent[Anthropic Claude Agent]
        
        Agent -- "Tool calls" --> MCP
        MCP -- "Tool results" --> Agent
        
        Agent -- "Final response" --> Scorer["Scoring Engine<br/>(Metrics / Custom)"]
    end
    
    Scorer -- "Produces" --> Report[SuiteReport]
    Report --> Output[CLI / Print]

    style Runner fill:#f9f,stroke:#333,stroke-width:2px
    style Agent fill:#bfb,stroke:#333,stroke-width:2px
    style MCP fill:#bbf,stroke:#333,stroke-width:2px
```

## Java: Agent Evaluation CLI

The Java component acts as a lightweight standalone execution engine (CLI) built with Spring Shell. It can evaluate any generic OpenAI-compatible chat-completions API using definitions loaded from a static JSON file.

```mermaid
flowchart LR
    User([User]) -- "Commands:<br/>eval run / list / report" --> CLI

    subgraph Java Application
        CLI[Spring Shell CLI]
        Engine[Evaluation Engine]
        Scorer["Scoring Methods<br/>EXACT/CONTAINS/REGEX"]
        
        CLI --> Engine
        Engine <--> Scorer
    end

    Config[sample-eval.json] -- "Loads Eval Cases" --> Engine
    
    Engine -- "HTTP /v1/chat/completions" --> LLM["OpenAI-Compatible<br/>API Endpoint"]
    LLM -- "Responses" --> Engine
    
    Engine -- "Formats Results" --> CLI

    style CLI fill:#f9f,stroke:#333,stroke-width:2px
    style Engine fill:#ff9,stroke:#333,stroke-width:2px
    style LLM fill:#bfb,stroke:#333,stroke-width:2px
```
