# Technical Specification: Production-Ready Modular AI Business Agent

## 1) Purpose and Scope
This document defines a production-ready AI Agent platform for day-to-day business operations (planning, scheduling, communications, analytics assistance, and operational execution support) with safety, modularity, and observability as first-class concerns.

The platform is designed for:
- **Human-supervised autonomy** for low-risk actions.
- **Strict least-privilege controls** for integrations and data operations.
- **Extensible skills architecture** to support new business workflows.
- **Reliable memory and retrieval** for context continuity across sessions.

---

## 2) Product Goals

### Primary Goals
1. Reduce routine operational overhead using AI-assisted execution.
2. Maintain a transparent decision loop (Plan-Act-Reflect).
3. Enforce safety boundaries and approval gates for destructive or high-impact actions.
4. Provide auditable logs and traces for every decision and tool call.

### Non-Goals (Phase 1)
- Fully unsupervised execution of high-risk financial or legal actions.
- Autonomous data deletion or irreversible system modifications.
- Direct model fine-tuning pipelines.

---

## 3) Recommended Tech Stack

### Core Runtime
- **Python 3.12+**
- **FastAPI** for backend API and tool orchestration
- **Pydantic v2** for strict schema validation
- **LangGraph** (preferred) for explicit stateful agent graph + control flow
  - Alternative: PydanticAI where simpler orchestration is preferred

### LLM Access
- Model provider abstraction via adapter layer:
  - OpenAI / Anthropic / Azure OpenAI (config-driven)
- Prompt/version registry for reproducibility

### Memory (RAG)
- **ChromaDB** for local/self-hosted deployments (default)
- Optional enterprise mode: **Pinecone**
- Embedding provider abstraction (OpenAI, Cohere, etc.)

### Frontend
- **Streamlit** (rapid internal operations UI, phase 1)
- Optional phase 2: React + Next.js for enterprise dashboard

### Integration Tools (initial)
- Google Calendar API
- Slack API and/or Discord API
- Email (Microsoft Graph/Gmail API)
- CRM (HubSpot/Salesforce via connector abstraction)
- Task tools (Asana, Trello, Jira)
- Internal SQL reporting tools (read-only by default)

### Infra & Ops
- Docker + docker-compose
- Redis (rate-limiting/caching/session state)
- PostgreSQL (metadata/audit store)
- OpenTelemetry + structured logging

---

## 4) High-Level Architecture

### Components
1. **API Layer (FastAPI)**
   - AuthN/AuthZ
   - Request validation
   - Session initiation and agent run invocation

2. **Agent Core (LangGraph)**
   - State machine with Plan → Act → Reflect loop
   - Tool routing and execution control
   - Policy and safety checks before each action

3. **Skills Layer**
   - Isolated skill modules implementing domain capabilities
   - Strict input/output contracts with Pydantic models
   - Examples: scheduling, finance summaries, communication drafting

4. **Memory Layer (RAG)**
   - Short-term memory (session state)
   - Long-term memory (vector store with metadata + retention policy)
   - Retrieval with citation payloads and confidence scoring

5. **Observability Layer**
   - Structured event logs
   - Trace IDs per run
   - Metrics: token usage, tool calls, latency, failures
   - Kill switch + loop guardrail

6. **Policy Engine**
   - Least-privilege enforcement
   - Risk scoring for proposed actions
   - HITL confirmation for sensitive operations

---

## 5) Agent Cognitive Loop (Plan-Act-Reflect)

### Plan
- Parse user intent and constraints.
- Retrieve relevant memories and contextual data.
- Generate explicit task plan with bounded steps.
- Assign risk tags per step (`low`, `medium`, `high`, `restricted`).

### Act
- Execute one step at a time.
- Select tool by capability map and policy eligibility.
- Validate tool inputs against schema.
- Record pre/post action state and outputs.

### Reflect
- Evaluate result correctness and completeness.
- Detect hallucination risk, tool failure, or policy violation.
- Decide to continue, re-plan, ask clarification, or escalate to HITL.

### Loop Controls
- `MAX_ITERATIONS` (default: 8)
- `MAX_TOOL_CALLS_PER_RUN` (default: 20)
- `MAX_RUNTIME_SECONDS` (default: 90)
- Stop reasons logged (`completed`, `timeout`, `kill_switch`, `policy_blocked`, `awaiting_human_approval`)

---

## 6) Safety, Compliance, and Guardrails

### Least Privilege (Hard Requirement)
- Every integration token should be scoped to minimal permissions:
  - Calendar: read/write events only (no account-wide admin actions)
  - Slack/Discord: channel-limited posting and reading
  - Database: read-only unless explicitly elevated for transaction-specific tasks

### Destructive Action Policy
- **No delete operations** (DB row/table, file, calendar event deletion, task deletion, message deletion) without explicit **HITL confirmation**.
- Agent must issue an approval request containing:
  - Action summary
  - Target resource
  - Reversibility status
  - Risk score
- Upon denial: action is permanently skipped for that run and logged.

### Sensitive Data Controls
- PII redaction in logs where possible
- Encrypted secrets in runtime environment
- Field-level data classification tags

### Prompt/Tool Injection Defenses
- Tool response sanitization
- Policy checks after tool output before next action
- Blocklist for unsafe instruction patterns

---

## 7) Memory System Specification (RAG)

### Memory Types
1. **Episodic**: conversation history + outcomes
2. **Procedural**: successful action patterns
3. **Semantic**: long-term business facts (policies, preferences, SOPs)

### Ingestion Pipeline
- Normalize content → chunk → embed → store with metadata:
  - `tenant_id`, `session_id`, `source`, `timestamp`, `sensitivity`, `ttl`

### Retrieval Pipeline
- Query rewrite (optional)
- Vector similarity search
- Metadata filtering by tenant and permission scope
- Re-ranking + confidence threshold
- Return top-k snippets + provenance

### Retention
- Configurable TTL and archival policy
- Right-to-delete workflows must be human-approved and audited

---

## 8) Skills Framework

### Design Principles
- One skill = one bounded domain capability
- No direct model calls inside tools unless required
- Strong schema contracts and deterministic behavior where possible

### Initial Skill Set
- `skills/scheduling.py`: calendar coordination, conflict checks, meeting prep
- `skills/finance.py`: cashflow summaries, invoice reminders, KPI snapshots (read-only)
- `skills/comms.py`: Slack/Discord drafting and send workflows with approval controls

### Skill Registration
- Central registry mapping:
  - capability name
  - required permissions
  - risk level
  - handler callable

---

## 9) API Contracts

### Key Endpoints
- `POST /v1/agent/run`
  - Starts an agent run with user request
- `GET /v1/agent/runs/{run_id}`
  - Retrieves run status, plan, logs, stop reason
- `POST /v1/agent/runs/{run_id}/approve`
  - HITL decision for gated actions
- `GET /v1/health`
  - Service health

### Request/Response Standards
- Pydantic models with strict typing
- Correlation ID in headers
- Idempotency key support for run creation

---

## 10) Observability and Operational Controls

### Logging
- JSON structured logs (`timestamp`, `level`, `run_id`, `tenant_id`, `component`, `event`)
- Separate audit log stream for policy decisions and approvals

### Metrics
- Request count, failure count, model latency, tool latency
- Loop iteration counts and safety-trigger frequencies

### Kill Switch
- Manual: admin endpoint toggles `AGENT_KILL_SWITCH=true`
- Automatic: triggers on repeated failures, budget breach, or anomaly score threshold
- Behavior: immediately halt execution and return safe status

---

## 11) Repository Blueprint (Target)

```text
business-agent/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes_agent.py
│   │   └── routes_health.py
│   ├── core/
│   │   ├── agent_core.py
│   │   ├── policy_engine.py
│   │   ├── tool_registry.py
│   │   ├── config.py
│   │   └── models.py
│   ├── memory/
│   │   ├── memory.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── skills/
│   │   ├── scheduling.py
│   │   ├── finance.py
│   │   └── comms.py
│   ├── integrations/
│   │   ├── google_calendar.py
│   │   ├── slack.py
│   │   ├── discord.py
│   │   └── crm.py
│   ├── observability/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── tracing.py
│   └── security/
│       ├── auth.py
│       ├── permissions.py
│       └── redaction.py
├── frontend/
│   └── streamlit_app.py
├── tests/
│   ├── test_agent_core.py
│   ├── test_policy_engine.py
│   ├── test_memory.py
│   └── test_skills_scheduling.py
├── scripts/
│   ├── seed_memory.py
│   └── run_local.sh
├── Spec.md
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## 12) Deployment and Runtime

### Containerization
- Single Docker image for backend + optional Streamlit service mode
- Non-root runtime user
- Healthcheck endpoint and graceful shutdown

### Environment Variables
- Model/API keys
- Vector DB settings
- OAuth credentials for integrations
- Policy toggles and thresholds

### Scaling
- Horizontal FastAPI replicas behind load balancer
- Shared state via Redis/PostgreSQL
- Queue-based async tool execution for long tasks (Celery/RQ)

---

## 13) Acceptance Criteria (Phase 1)
1. Agent can execute a request using Plan-Act-Reflect with traceable logs.
2. Calendar and Slack integration works with scoped credentials.
3. Memory retrieval improves answer quality with source context.
4. Kill switch halts any active run safely.
5. Any delete/destructive action is blocked pending explicit HITL approval.
6. Full run audit record is queryable by `run_id`.

---

## 14) Next Build Steps
1. Scaffold repository and configuration baseline.
2. Implement `agent_core.py` with LangGraph state machine.
3. Implement `memory.py` with Chroma-backed RAG.
4. Implement `skills/scheduling.py` as first production skill.
5. Add policy engine + HITL approval endpoints.
6. Add tests, Dockerization, and deployment docs.

