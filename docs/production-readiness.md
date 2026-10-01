# Production readiness and integration boundary

## Implemented in this repository

- PostgreSQL and Redis services for local Compose; Alembic schema revisions.
- Optional bearer API keys with analyst and operator roles. Compose requires both distinct keys; local SQLite defaults to synthetic demo mode.
- Redis-backed rate limiting with an in-process fallback, JSON request logs, normalized-route request counters, request IDs, and `/readyz`.
- HMAC-SHA256 sandbox partner event boundary with partner identity, a five-minute timestamp window, event ID idempotency, and transaction-state validation.
- Deterministic risk/rule engines, optional estimator adapter, relational transaction relationship graph, and outcome feedback snapshots.

## Required before any real deployment

1. Select a cloud provider/account and deployment region; this repository has not been deployed to a cloud environment.
2. Put the service behind TLS termination and a trusted reverse proxy. Restrict database, Redis, metrics, and administrative ports to private networks.
3. Move API keys, partner HMAC secrets, database credentials, and any future model credentials into the selected provider's secret manager. Define rotation and revocation operations.
4. Replace shared API keys with the institution's approved identity system, user-level authorization, tenant boundaries, and an audited reviewer identity source. Current API roles distinguish analyst and operator only; they do not provide tenant isolation.
5. Obtain explicit authorization, event contracts, signing-key lifecycle, idempotency guarantees, and sandbox certification from each bank/PSP/merchant. The partner-event endpoint is only a signed event boundary; no live UPI, bank, or payment-processor connection exists.
6. Define production database backups, restore drills, retention/deletion policies, incident response, alert thresholds, tracing, and multi-instance metrics aggregation. Current `/metrics` counters are process-local. The Compose file uses health checks and starts the UI after backend readiness.
7. Establish lawful, consented, representative labels and validation methodology before enabling any trained model. Current scores are heuristics and outcome labels begin as `UNVERIFIED`; an operator can record a second-review verification. Only verified legitimate/unauthorized labels enter a simple retrospective threshold count; no automatic training occurs.
8. Validate financial operations, settlement/reversal semantics, legal/compliance controls, and reconciliation source-of-truth with the authorized provider before any operational use.

## Current limits

The relational graph only reports shared IDs in the latest bounded synthetic transaction sample; it does not infer ownership or wrongdoing. The outcome loop stores the risk snapshot alongside reviewer-reported labels for later evaluation. It does not change the model. Cloud deployment, production identity, partner authorization, and live network integration remain external prerequisites, not completed features.
