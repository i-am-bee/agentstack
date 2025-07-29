# BeeAI SDK

## Examples

The examples connect to the BeeAI Platform for LLM inteference.

Run using:

```bash
uv run examples/agent.py
```

Connect to the agent using the CLI:

```bash
uv run examples/cli.py
```

## Plan

- `beeai_sdk`
    - `a2a`:
        - `extensions`: Shared definitions for A2A extensions
            - `services`: Dependency injection extensions for external services
                - `llm`
                - `embedding`
                - `docling`
                - `file_store`
                - `vector_store`
            - `ui`: User interface extensions for BeeAI Platform UI
                - `trajectory`
                - `citations`
            - `history`: store and allow requesting the full history of the context
    - `server`
        - `context_storage`: store data associated with context_id
        - `wrapper`: conveniently build A2A agents -- opinionated on how tasks work, `yield`-semantics, autowired
          services
        - `services`: clients for external services
            - `llm`: OpenAI-compatible chat LLM
            - `embedding`: OpenAI-compatible embedding
            - `text_extraction`: Docling-compatible text extraction
            - `file_store`: S3-compatible file storage
            - `vector_store`: some vector store?
    - `client`
        - ?
