# Real-Time Financial Transaction Intelligence Platform

**Know what happens to your money, the moment it moves.**

Phase 1 establishes an auditable transaction foundation. Phase 2 adds user, merchant, device, beneficiary, mandate, and descriptive transaction context. Phase 3 adds deterministic demo rules, anomaly signals, weighted risk fusion, and evidence-based explanations. Phase 4 adds a synthetic event simulator, WebSocket stream, Redis pub/sub relay, database-backed dashboard summary, and a Next.js live overview dashboard. Phase 5 adds explicit mandate assessment, evidence-backed reconciliation, transaction investigations, and an investigation detail page with timeline and reconciliation controls. Phase 6 adds a model adapter boundary, feature engineering, deterministic evidence summaries, and constrained natural-language transaction search. No ML model or external LLM is configured; synthetic events are not used as training labels. Phase 7 adds role-scoped bearer API keys, request rate limiting, JSON request logs, request metrics, database readiness checks, signed sandbox partner events, and Alembic migrations. Phase 8 adds a bounded relational relationship graph and an audited outcome feedback loop with explicit operator verification; it does not train a model automatically. All data created by the API is marked `SYNTHETIC`; this project does not connect to live UPI or use real banking credentials.

## Run locally

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL = "sqlite:///./local.db"
alembic upgrade head
uvicorn app.main:app --reload
```

For the full PostgreSQL, Redis, backend, and frontend stack, run `./scripts/init_env.ps1` in PowerShell to generate a private `.env` with random database, Redis, partner, and API credentials, then run `docker compose up --build` from the project root. Enter the analyst or operator API key in the dashboard to use it; the key stays in the current browser session. Read the generated values from `.env` locally and do not paste them into source files or commit them. The script refuses to overwrite an existing `.env`. The dashboard is at `http://localhost:3000`; API docs are at `http://localhost:8000/docs`. Docker is required for the composed stack.

## Deploy to Render

After pushing this repository to GitHub, use the one-click link below. Render reads `render.yaml` and provisions the frontend, API, PostgreSQL, and Redis-compatible Key Value services. Enter two different API keys of at least 32 characters when prompted, then use either key in the dashboard's API key field.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/sriyathid-commits/financial-intelligence)

The Blueprint uses free plans for a demo. Render free PostgreSQL expires after 30 days, and free Key Value does not persist data; upgrade both before keeping important data. This application handles synthetic events only and is not connected to live payment networks.

To run only the backend locally, set `DATABASE_URL` to a SQLite URL as shown above. Redis is optional for one-process WebSocket delivery; when available, the backend publishes and subscribes on `financial.transaction.events` so events can be relayed between backend instances. Simulator controls are `POST /api/v1/simulator/start`, `POST /api/v1/simulator/stop`, and `GET /api/v1/simulator/status`.

## Tests

From `backend/`: `python -m pytest` (tests use isolated in-memory SQLite).

## Security and operations

Compose requires authentication and distinct 48-byte random analyst/operator API keys; `scripts/init_env.ps1` creates them. Analysts can read and search; operators can write and control reconciliation/simulation. Local SQLite development defaults to demo mode unless `AUTH_REQUIRED=true`. The sandbox partner endpoint uses HMAC-SHA256 over `timestamp.event-id.raw-body`, a five-minute timestamp window, and database idempotency. It accepts only configured sandbox partner identity/secret values and does not connect to payment networks.

Apply schema revisions with Alembic (`alembic upgrade head`). `/readyz` checks database readiness and required auth configuration. `/metrics` reports in-process Prometheus text counters. JSON request logs include normalized route, response code, latency, and generated request ID. Rate limits use Redis when connected and a process-local fallback otherwise.

## API highlights

- `POST /api/v1/transactions`
- `GET /api/v1/transactions`
- `GET /api/v1/transactions/{transaction_id}`
- `GET /api/v1/transactions/{transaction_id}/timeline`
- `GET /api/v1/transactions/{transaction_id}/context`
- `GET /api/v1/transactions/{transaction_id}/risk`
- `GET /api/v1/transactions/{transaction_id}/explanation`
- `POST /api/v1/users`, `/merchants`, `/devices`, `/beneficiaries`, `/mandates`
- `GET /api/v1/mandates`, `/mandates/{mandate_id}`, `/mandates/{mandate_id}/assessment`
- `GET /api/v1/investigations/{transaction_id}` and `/assistant-summary`
- `POST /api/v1/queries/transactions` (constrained deterministic filters; not an LLM)
- `GET /api/v1/graph/transactions/{transaction_id}`
- `POST/GET /api/v1/investigations/{transaction_id}/outcomes`
- `GET /api/v1/learning/summary`
- `POST /api/v1/partner-events` (signed synthetic partner events)
- `GET /readyz`, `GET /metrics`
- `GET /api/v1/reconciliation/{transaction_id}`
- `POST /api/v1/reconciliation/{transaction_id}/start` then `/evidence` with merchant confirmation or reversal evidence
- `POST /api/v1/transactions/{transaction_id}/transitions`
- `GET /api/v1/dashboard/summary`
- `POST /api/v1/simulator/start`, `/api/v1/simulator/stop`; `GET /api/v1/simulator/status`
- `WS /ws/transactions`
- `GET /health`

Money is represented as `Decimal` and persisted as SQL `NUMERIC(18,2)`. State changes are validated and recorded as transaction events. PostgreSQL is configured by Docker Compose; the local application defaults to SQLite unless `DATABASE_URL` is set.

## Production readiness boundary

This repository provides local Compose and integration boundaries, not a cloud deployment. It has no selected cloud account, TLS/reverse proxy, managed secret store, SSO/MFA identity provider, tenant isolation, payment-network credentials, or partner authorization. Review `docs/production-readiness.md` before any external deployment. Graph links and outcome feedback are synthetic-platform records; feedback labels are unverified until a separate operator review and never initiate model training.
