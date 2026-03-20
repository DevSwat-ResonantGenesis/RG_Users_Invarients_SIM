# RG Users Invariants SIM

User-facing Hash Sphere state-space invariants and physics simulation service for Genesis2026.

## Overview

This is a standalone microservice extracted from the monolithic `state_physics_service`. It provides:

- **Identity Layer (DSID)** — "who exists?"
- **State/Memory Layer** — "what happened and what persists?"
- **Economic/Temporal Layer** — "what matters and what survives?"
- **Physics simulation** — force-directed graph with mass, charge, temperature, entropy
- **Core invariants** — mass conservation, energy conservation, identity uniqueness, causality, trust bounds

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8091
```

## Docker

```bash
docker build -t rg_users_invarients_sim .
docker run -p 8091:8091 rg_users_invarients_sim
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://shared_redis:6379/0` | Redis connection |

## API Endpoints

- `GET /health` — Health check
- `GET /` — Frontend UI
- `GET /api/v1/status` — Service status
- `GET /api/state` — Hash Sphere state for current user
- `GET /api/nodes` — List nodes
- `POST /api/identity` — Create identity
- `GET /api/metrics` — Get metrics
- `POST /api/simulate` — Run simulation

## Port

**8091**
