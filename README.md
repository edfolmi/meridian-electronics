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
| `FRONTEND_ORIGIN` | No | CORS origin for local/prod frontend |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Browser-visible FastAPI base URL |

## Milestones

### Milestone 1: Project Scaffold

Suggested commit message:

```text
chore: scaffold Next.js and FastAPI chatbot prototype
```

Included:

- Clean folder structure
- README setup instructions
- `.env.example`
- FastAPI health endpoint
- Next.js chat page placeholder

### Milestone 2: MCP Discovery

Suggested commit message:

```text
feat: add MCP client and tool discovery endpoint
```

Included:

- `backend/app/mcp/client.py` for streamable HTTP JSON-RPC calls
- `GET /api/mcp/tools` discovery endpoint
- Graceful error response when MCP is unavailable
- Basic logs showing discovered tool names

### Milestone 3: Chat Backend

Suggested commit message:

```text
feat: implement LLM chat orchestration with MCP tools
```

Included:

- `POST /api/chat` FastAPI endpoint
- OpenRouter `AsyncOpenAI` client with `OPENROUTER_MODEL`
- Meridian-specific system prompt
- Tool-call loop that discovers MCP tools and executes requested tool calls
- Practical failures for missing API keys, LLM errors, MCP errors, and malformed tool arguments

### Milestone 4: Customer Chat UI

Suggested commit message:

```text
feat: build customer support chat interface
```

Included:

- Next.js chat interface with message history
- Loading and error states
- Dedicated secure sign-in form for authenticated workflows
- Tool-call badges for MCP-backed responses
- Calls FastAPI `POST /api/chat`
- No hardcoded product, customer, or order answers

### Milestone 5: Scenario Validation

Suggested commit message:

```text
test: validate core Meridian support workflows
```

Included:

- Backend tests for tool parsing, MCP response decoding, and API routing
- `backend/scripts/validate_scenarios.py` for product availability, customer authentication, and order history
- Uses provided assessment test account through backend-only MCP verification

### Milestone 6: Deployment Readiness

Suggested commit message:

```text
chore: prepare deployment configuration and final README
```

Included:

- Docker deployment path for HuggingFace Spaces
- Production environment variable checklist
- Architecture summary and limitations
- Video notes in `docs/video-notes.md`

### Security Update: Dedicated Authentication Flow

Suggested commit message:

```text
fix: route customer authentication outside LLM chat
```

Included:

- `POST /api/auth/sign-in` verifies email/PIN through MCP
- Frontend secure sign-in form sends credentials directly to the backend
- Chat requests include only safe authenticated customer session context
- LLM tool list excludes `verify_customer_pin`
- Prompt explicitly forbids asking for credentials in chat

### Optional Guardrails and Tracing

Suggested commit message:

```text
feat: add OpenRouter guardrails and optional OpenAI tracing
```

Included:

- Llama Guard input safety check through OpenRouter
- Low-cost evaluator model to detect account/order-history intent before main chat
- Early sign-in prompt for unauthenticated account-specific requests
- Optional OpenAI Agents SDK tracing with metadata-only custom spans
- No raw PIN, chat content, tool results, customer history, or order details are intentionally logged in traces

## Known Limitations

- Chat requires a valid OpenRouter key.
- The assistant only verifies product, customer, and order data through MCP tools. If the tools are unavailable, it should say it cannot verify the answer.
- `create_order` is available through MCP, but a real production checkout should add explicit confirmation, stronger authorization, payment flow integration, rate limits, and audit logging.
- The prototype is stateless between API requests except for visible chat history. Production should add server-side session memory for authenticated customer context.
- Formal evaluation and durable tracing are intentionally out of scope for the first production prototype.
