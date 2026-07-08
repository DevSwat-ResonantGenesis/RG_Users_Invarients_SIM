# RG Users Invariants SIM

> **Part of the [ResonantGenesis](https://dev-swat.com) platform** — user-facing Hash Sphere state-space invariants and physics simulation.

[![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()
[![Docker: rg_users_invarients_sim](https://img.shields.io/badge/Docker-rg__users__invarients__sim-blue.svg)]()
[![Port: 8091](https://img.shields.io/badge/Port-8091-orange.svg)]()
[![License: RG Source Available](https://img.shields.io/badge/License-RG%20Source%20Available-blue.svg)](LICENSE.txt)

User-facing Hash Sphere state-space invariants and physics simulation service for Genesis2026. Manages identity creation (DSID), state persistence, economic layers, and force-directed graph physics. Deployed as standalone Docker container `rg_users_invarients_sim`.

## Architecture

```
User → Nginx → Gateway → rg_users_invarients_sim (this service, port 8091)
                              ├── Redis (state caching, locks)
                              └── Frontend UI (embedded visualization)

Internal consumers:
  rg_internal_invarients_sim → this service (Hash Sphere state for governance)
  rg_agentic_chat            → this service (state_physics tools proxy)
  chat_service               → this service (DSID creation, memory ingestion)
```

## Features

- **Identity Layer (DSID)** — "who exists?"
- **State/Memory Layer** — "what happened and what persists?"
- **Economic/Temporal Layer** — "what matters and what survives?"
- **Physics simulation** — force-directed graph with mass, charge, temperature, entropy
- **Core invariants** — mass conservation, energy conservation, identity uniqueness, causality, trust bounds
- **Frontend UI** — embedded visualization at root `/`

## Quick Start

```bash
# Clone
git clone git@github-devswat:DevSwat-ResonantGenesis/RG_Users_Invarients_SIM.git
cd RG_Users_Invarients_SIM

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
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

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | Frontend UI (embedded visualization) |
| `GET` | `/api/v1/status` | Service status |
| `GET` | `/api/state` | Hash Sphere state for current user |
| `GET` | `/api/nodes` | List nodes |
| `POST` | `/api/identity` | Create identity (DSID) |
| `GET` | `/api/metrics` | Get metrics |
| `POST` | `/api/simulate` | Run physics simulation |

## Gateway Integration

The gateway proxies state physics requests to this standalone service:
```
/state-physics/*        → http://rg_users_invarients_sim:8091/*
/api/v1/state-physics/* → http://rg_users_invarients_sim:8091/*
```

## Related Modules

| Module | Repo | Relationship |
|--------|------|-------------|
| Internal Invariants SIM | [`RG_Internal_Invarients_SIM`](https://github.com/DevSwat-ResonantGenesis/RG_Internal_Invarients_SIM) | RARA reads Hash Sphere state for governance decisions |
| Registered Users Agentic Chat | [`RG_Registered_Users_Agentic_Chat`](https://github.com/DevSwat-ResonantGenesis/RG_Registered_Users_Agentic_Chat) | Chat `state_physics_*` tools proxy to this service |
| AST Analysis | [`RG_AST_analysis`](https://github.com/DevSwat-ResonantGenesis/RG_AST_analysis) | Not directly connected |
| Unified LLM Client | [`RG_UnifiedLLMClient`](https://github.com/DevSwat-ResonantGenesis/RG_UnifiedLLMClient) | Not used by this service |

## Deployment Status

- **Status**: ✅ **Production** — deployed as standalone Docker container `rg_users_invarients_sim`
- **Extracted from**: `genesis2026_production_backend/state_physics_service` (entire directory deleted from monolith)
- **Server path**: `/home/deploy/RG_Users_Invarients_SIM` (cloned from DevSwat GitHub)
- **Docker service**: `rg_users_invarients_sim` in `docker-compose.unified.yml`
- **Port**: 8091 (internal Docker network)

---

**Organization**: [DevSwat-ResonantGenesis](https://github.com/DevSwat-ResonantGenesis)
**Platform**: [dev-swat.com](https://dev-swat.com)
