# consequence

Agent evaluation tool – a CLI built with **Java 17**, **Spring Shell**, and **Maven**.

Point it at any [OpenAI-compatible](https://platform.openai.com/docs/api-reference/chat) chat-completions endpoint (e.g. Ollama, OpenAI, vLLM) and run structured evaluation suites to measure agent quality.

---

## Requirements

| Tool | Version |
|------|---------|
| JDK  | 17+     |
| Maven | 3.8+   |

---

## Build

```bash
mvn clean package -q
```

This produces a self-contained fat-jar at `target/consequence-0.1.0-SNAPSHOT.jar`.

---

## Configuration

Configuration is read from `src/main/resources/application.yml` or from environment variables:

| Environment variable       | Default                          | Description                              |
|---------------------------|----------------------------------|------------------------------------------|
| `AGENT_BASE_URL`          | `http://localhost:11434/v1`      | Base URL of the chat-completions endpoint |
| `AGENT_API_KEY`           | *(empty)*                        | Bearer token / API key (optional)         |
| `AGENT_MODEL`             | `llama3`                         | Model name sent in the request body       |
| `AGENT_TIMEOUT_SECONDS`   | `60`                             | HTTP call timeout                         |

---

## Usage

### Interactive shell

```bash
java -jar target/consequence-0.1.0-SNAPSHOT.jar
```

```
shell:> eval list --suite sample-eval.json
shell:> eval run  --suite sample-eval.json
shell:> eval report --suite sample-eval.json
```

### Non-interactive (script mode)

```bash
java -jar target/consequence-0.1.0-SNAPSHOT.jar \
     --spring.shell.interactive.enabled=false    \
     --spring.shell.script.enabled=true          \
     eval run --suite path/to/my-suite.json
```

---

## Eval suite format

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

---

## Run tests

```bash
mvn test
```