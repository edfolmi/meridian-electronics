# Meridian Electronics Support Chatbot

Production-minded prototype for a Meridian Electronics customer support chatbot.

The app uses:

- Next.js frontend for the customer chat UI
- FastAPI backend API layer
- MCP tool integration against Meridian's order/product MCP server
- OpenRouter through the OpenAI-compatible async client
- Environment-based configuration for secrets and deploy settings

## Architecture

```text
frontend/  Next.js customer chat UI
backend/   FastAPI API, chat orchestration, MCP client, tests
```

Backend modules are intentionally small:

- `backend/app/api/` HTTP routes
- `backend/app/core/` config and logging helpers
- `backend/app/llm/` prompt and chat orchestration
- `backend/app/mcp/` MCP JSON-RPC client
- `backend/app/schemas/` request/response models
- `backend/tests/` focused backend tests

## Local Setup

1. Copy environment values:

```bash
cp .env.example .env
```

2. Fill `OPENROUTER_API_KEY` in `.env`.

3. Run the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

4. Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

5. Open `http://localhost:3000`.

## Validation

Run focused backend tests:

```bash
cd backend
uv run pytest
```

Run live MCP scenario checks:

```bash
cd backend
uv run python scripts/validate_scenarios.py
```

## Deployment

### HuggingFace Spaces Docker

1. Create a new HuggingFace Space with the Docker SDK.
2. Push this repository to the Space.
3. Add Space secrets:

```text
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=gpt-4o-mini
MCP_SERVER_URL=https://order-mcp-74afyau24q-uc.a.run.app/mcp
```

4. The included `Dockerfile` builds the Next.js frontend, runs FastAPI on internal port `8000`, and serves the customer UI on Space port `7860`.

For separate frontend/backend hosting, deploy `backend/` as a FastAPI service and set:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-backend.example.com
FRONTEND_ORIGIN=https://your-frontend.example.com
```

### Production Environment Checklist

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`
- `MCP_SERVER_URL`
- `FRONTEND_ORIGIN`
- `BACKEND_API_BASE_URL` when using the Next.js proxy
- `NEXT_PUBLIC_API_BASE_URL` when the browser calls FastAPI directly
- `LOG_LEVEL`

## Screenshots

Add screenshots after deployment:

- Chat landing state
- Product availability response with MCP tool badge
- Authenticated order history response

## Environment Variables

| Name | Required | Description |
| --- | --- | --- |
| `MCP_SERVER_URL` | Yes | Meridian MCP streamable HTTP endpoint |
| `OPENROUTER_API_KEY` | Yes for chat | OpenRouter API key |
| `OPENROUTER_MODEL` | No | Cost-effective OpenRouter model, default `gpt-4o-mini` |
| `OPENROUTER_BASE_URL` | No | Default `https://openrouter.ai/api/v1` |
| `GUARDRAILS_ENABLED` | No | Enables OpenRouter guardrail/evaluator checks |
| `SAFETY_GUARDRAIL_ENFORCE` | No | Set `true` to block Llama Guard unsafe verdicts; default keeps it advisory |
| `OPENROUTER_GUARDRAIL_MODEL` | No | Llama Guard model used for safety classification |
| `OPENROUTER_EVALUATOR_MODEL` | No | Low-cost evaluator model for account-intent classification |
| `OPENAI_API_KEY` | No | Enables OpenAI trace export when tracing is enabled |
| `OPENAI_TRACING_ENABLED` | No | Set `true` to send metadata-only traces to OpenAI |
| `LANGFUSE_TRACING_ENABLED` | No | Set `true` to send metadata-only traces to Langfuse |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key |
| `LANGFUSE_BASE_URL` | No | Langfuse host, default `https://cloud.langfuse.com` |
| `FRONTEND_ORIGIN` | No | CORS origin for local/prod frontend |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Browser-visible FastAPI base URL |

## Screenshots

Refer to the folder named screenshots for tracing observability and platform in action screenshots.
