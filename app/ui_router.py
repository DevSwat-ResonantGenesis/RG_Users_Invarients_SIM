from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel

from .agent import AgentConfig, HashSphereAgent
from .analyzer import HashSphereAnalyzer
from .entropy import EntropyConfig, EntropyEngine
from .models import HashSphereState, NodeType
from .physics import PhysicsConfig, PhysicsEngine


router = APIRouter(prefix="/api", tags=["state-physics-ui"])


@dataclass
class Universe:
    analyzer: HashSphereAnalyzer
    physics: PhysicsEngine
    entropy: EntropyEngine
    entropy_enabled: bool = True
    agent: Optional[HashSphereAgent] = None
    agents: List[HashSphereAgent] = None
    memory_cost_multiplier: float = 1.0
    metrics_history: List[Dict[str, Any]] = None


_universe: Optional[Universe] = None

_universes: Dict[str, Universe] = {}


def _universe_key_from_request(request: Request) -> str:
    # Prefer explicit State Physics universe id.
    state_physics_universe_id = (request.headers.get("x-state-physics-universe-id") or "").strip()
    if state_physics_universe_id:
        return f"sp-universe:{state_physics_universe_id}"

    # Backward-compatible fallback: x-universe-id (Hash Sphere identity universe).
    universe_id = (request.headers.get("x-universe-id") or "").strip()
    if universe_id:
        return f"universe:{universe_id}"

    org_id = (request.headers.get("x-org-id") or "").strip()
    if org_id:
        return f"org:{org_id}"

    user_id = (request.headers.get("x-user-id") or "").strip()
    if user_id:
        return f"user:{user_id}"

    return "public"


def _create_universe(use_demo: bool = True) -> Universe:
    """Create a new universe. If use_demo=False, creates empty universe."""
    analyzer = HashSphereAnalyzer()
    universe = Universe(
        analyzer=analyzer,
        physics=PhysicsEngine(),
        entropy=EntropyEngine(),
        entropy_enabled=True,
        agent=None,
        agents=[],
        memory_cost_multiplier=1.0,
        metrics_history=[],
    )
    if use_demo:
        _seed_demo(universe, num_users=30, num_transactions=80, num_services=5)
    return universe


async def _create_user_universe(user_id: str, org_id: str = "") -> Universe:
    """Create a universe populated with real user data from backend services."""
    from .user_data_loader import load_user_universe, create_empty_universe_for_new_user
    
    analyzer = HashSphereAnalyzer()
    universe = Universe(
        analyzer=analyzer,
        physics=PhysicsEngine(),
        entropy=EntropyEngine(),
        entropy_enabled=True,
        agent=None,
        agents=[],
        memory_cost_multiplier=1.0,
        metrics_history=[],
    )
    
    try:
        # Load real user data from blockchain and memory services
        await load_user_universe(analyzer, user_id, org_id)
    except Exception as e:
        # If loading fails, create empty universe for new user
        print(f"Failed to load user data for {user_id}: {e}")
        create_empty_universe_for_new_user(analyzer, user_id)
    
    return universe


def get_universe(request: Request) -> Universe:
    """Get or create universe for request (sync version, uses demo data)."""
    key = _universe_key_from_request(request)
    universe = _universes.get(key)
    if universe is None:
        universe = _create_universe(use_demo=True)
        _universes[key] = universe
    return universe


async def get_user_universe(request: Request) -> Universe:
    """Get or create universe with REAL user data (async version)."""
    key = _universe_key_from_request(request)
    universe = _universes.get(key)
    
    if universe is None:
        user_id = (request.headers.get("x-user-id") or "").strip()
        org_id = (request.headers.get("x-org-id") or "").strip()
        
        if user_id and user_id != "anonymous":
            # Load real user data
            universe = await _create_user_universe(user_id, org_id)
        else:
            # Anonymous users get demo data
            universe = _create_universe(use_demo=True)
        
        _universes[key] = universe
    
    return universe


def _state_to_ui_dict(state: HashSphereState, analyzer: HashSphereAnalyzer) -> Dict[str, Any]:
    violations = analyzer.check_invariants()
    nodes = [n.to_dict() for n in state.nodes.values()]
    edges = [e.to_dict() for e in state.edges.values()]

    total_value = sum(n.value for n in state.nodes.values())
    avg_trust = (
        sum(n.trust_score for n in state.nodes.values()) / max(len(state.nodes), 1)
    )
    avg_temp = (
        sum(n.temperature for n in state.nodes.values()) / max(len(state.nodes), 1)
    )

    metrics = {
        "node_count": len(state.nodes),
        "edge_count": len(state.edges),
        "total_mass": state.total_mass,
        "total_value": total_value,
        "average_trust": avg_trust,
        "average_temperature": avg_temp,
        "entropy": state.entropy,
        "invariant_violations": len(violations),
    }

    invariants = [inv.to_dict() for inv in analyzer.invariants.values()]
    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": metrics,
        "invariants": invariants,
        "violations": violations,
    }


def _agent_status(agent: HashSphereAgent) -> Dict[str, Any]:
    node = agent.node
    return {
        "name": agent.config.name,
        "status": (node.status.value if node else "inactive"),
        "value": (node.value if node else 0.0),
        "trust": (node.trust_score if node else 0.0),
        "successful_transactions": agent.memory.successful_transactions,
        "failed_transactions": agent.memory.failed_transactions,
        "last_action": agent.last_action,
    }


def _seed_demo(universe: Universe, num_users: int, num_transactions: int, num_services: int) -> None:
    a = universe.analyzer
    a.state = HashSphereState()
    a.add_identity("core_system", node_type=NodeType.SERVICE, initial_trust=0.8, initial_value=500)

    users = []
    for i in range(num_users):
        users.append(
            a.add_identity(
                f"user_{i}",
                node_type=NodeType.USER,
                initial_trust=0.4,
                initial_value=100 + (i % 10) * 20,
            )
        )

    services = []
    for i in range(num_services):
        services.append(
            a.add_identity(
                f"service_{i}",
                node_type=NodeType.SERVICE,
                initial_trust=0.7,
                initial_value=200 + (i % 5) * 50,
            )
        )

    dsids = [n.dsid for n in users + services if n.dsid]
    if len(dsids) >= 2:
        import random

        for _ in range(num_transactions):
            from_dsid, to_dsid = random.sample(dsids, 2)
            amount = random.uniform(0.5, 20.0)
            try:
                a.add_transaction(from_dsid, to_dsid, amount)
            except Exception:
                continue

    a.state.entropy = a.state.compute_entropy()


class SimulateRequest(BaseModel):
    steps: int = 1


class GalaxyRequest(BaseModel):
    num_users: int = 500
    num_transactions: int = 1500
    num_services: int = 10
    enable_agent: bool = True
    enable_entropy: bool = True


class PhysicsConfigRequest(BaseModel):
    gravity_constant: Optional[float] = None
    repulsion_constant: Optional[float] = None
    spring_constant: Optional[float] = None
    damping: Optional[float] = None


class EntropyConfigRequest(BaseModel):
    position_noise: Optional[float] = None
    velocity_noise: Optional[float] = None
    trust_decay: Optional[float] = None
    value_decay: Optional[float] = None
    activity_probability: Optional[float] = None


def _compute_asymmetry(universe: Universe) -> Tuple[float, str]:
    state = universe.analyzer.state
    nodes = list(state.nodes.values())
    if not nodes:
        return 0.0, "empty"

    # Trust variance and value inequality are the core asymmetry signals.
    trusts = [n.trust_score for n in nodes]
    avg_trust = sum(trusts) / len(trusts)
    trust_var = sum((t - avg_trust) ** 2 for t in trusts) / len(trusts)

    values = sorted([max(0.0, n.value) for n in nodes])
    total = sum(values)
    if total <= 0:
        gini = 0.0
    else:
        n = len(values)
        gini = (
            sum((2 * i - n - 1) * v for i, v in enumerate(values, 1)) / (n * total)
        )
        gini = abs(gini)

    # Normalize into a 0..1-ish score.
    score = max(0.0, min(1.0, (trust_var * 10.0) + (gini * 0.7)))
    if score >= 0.2:
        interpretation = "emergence_possible"
    elif score < 0.05:
        interpretation = "system_frozen"
    else:
        interpretation = "unstable"
    return score, interpretation


@router.get("/state")
async def api_state(request: Request):
    # Use async version to load real user data
    universe = await get_user_universe(request)
    return _state_to_ui_dict(universe.analyzer.state, universe.analyzer)


@router.post("/reset")
async def api_reset(request: Request):
    key = _universe_key_from_request(request)
    # Reset with real user data
    user_id = (request.headers.get("x-user-id") or "").strip()
    org_id = (request.headers.get("x-org-id") or "").strip()
    
    if user_id and user_id != "anonymous":
        _universes[key] = await _create_user_universe(user_id, org_id)
    else:
        _universes[key] = _create_universe(use_demo=True)
    
    universe = _universes[key]
    return {"success": True, "state": _state_to_ui_dict(universe.analyzer.state, universe.analyzer)}


@router.post("/simulate")
async def api_simulate(request: Request, payload: SimulateRequest = Body(...)):
    # Use async version to ensure user data is loaded
    universe = await get_user_universe(request)
    steps = max(1, int(payload.steps))

    instabilities: List[Dict[str, Any]] = []
    for _ in range(steps):
        if universe.entropy_enabled:
            universe.analyzer.state = universe.entropy.inject_entropy(universe.analyzer.state)
        universe.analyzer.state = universe.physics.step(universe.analyzer.state)

        # Step single agent
        if universe.agent is not None:
            try:
                universe.agent.step()
            except Exception as e:
                instabilities.append({"type": "agent_step_error", "message": str(e)})

        # Step multi agents
        if universe.agents:
            for ag in list(universe.agents):
                try:
                    ag.step()
                except Exception as e:
                    instabilities.append({"type": "agent_step_error", "message": str(e)})

    state_dict = _state_to_ui_dict(universe.analyzer.state, universe.analyzer)
    entropy_metrics = universe.entropy.get_entropy_metrics(universe.analyzer.state)

    agent_status: Optional[Dict[str, Any]] = None
    if universe.agent is not None:
        agent_status = _agent_status(universe.agent)

    return {
        "state": state_dict,
        "entropy": entropy_metrics,
        "agent": agent_status,
        "instabilities": instabilities,
    }


@router.post("/physics/config")
async def api_physics_config(request: Request, payload: PhysicsConfigRequest = Body(...)):
    universe = await get_user_universe(request)
    cfg = universe.physics.config
    if payload.gravity_constant is not None:
        cfg.gravity_constant = float(payload.gravity_constant)
    if payload.repulsion_constant is not None:
        cfg.repulsion_constant = float(payload.repulsion_constant)
    if payload.spring_constant is not None:
        cfg.spring_constant = float(payload.spring_constant)
    if payload.damping is not None:
        cfg.damping = float(payload.damping)
    return {"success": True, "config": cfg.__dict__}


@router.post("/entropy/config")
async def api_entropy_config(request: Request, payload: EntropyConfigRequest = Body(...)):
    universe = await get_user_universe(request)
    cfg = universe.entropy.config
    if payload.position_noise is not None:
        cfg.position_noise = float(payload.position_noise)
    if payload.velocity_noise is not None:
        cfg.velocity_noise = float(payload.velocity_noise)
    if payload.trust_decay is not None:
        cfg.trust_decay = float(payload.trust_decay)
    if payload.value_decay is not None:
        cfg.value_decay = float(payload.value_decay)
    if payload.activity_probability is not None:
        cfg.activity_probability = float(payload.activity_probability)
    return {"success": True, "config": cfg.__dict__}


@router.post("/entropy/perturbation")
async def api_entropy_perturbation(request: Request, magnitude: float = 1.0):
    universe = await get_user_universe(request)
    event = universe.entropy.create_perturbation_event(universe.analyzer.state, magnitude=magnitude)
    return {"success": True, "event": event}


@router.post("/entropy/toggle")
async def api_entropy_toggle(request: Request, enabled: bool = True):
    universe = await get_user_universe(request)
    universe.entropy_enabled = bool(enabled)
    return {"success": True, "entropy_enabled": universe.entropy_enabled}


@router.get("/asymmetry")
async def api_asymmetry(request: Request):
    universe = await get_user_universe(request)
    score, interpretation = _compute_asymmetry(universe)
    return {"asymmetry_score": score, "interpretation": interpretation}


@router.post("/demo")
async def api_demo(request: Request, num_users: int = 30, num_transactions: int = 80):
    universe = await get_user_universe(request)
    _seed_demo(universe, num_users=num_users, num_transactions=num_transactions, num_services=5)
    return _state_to_ui_dict(universe.analyzer.state, universe.analyzer)


@router.post("/galaxy")
async def api_galaxy(request: Request, payload: GalaxyRequest = Body(...)):
    universe = await get_user_universe(request)
    _seed_demo(
        universe,
        num_users=int(payload.num_users),
        num_transactions=int(payload.num_transactions),
        num_services=int(payload.num_services),
    )
    universe.entropy_enabled = bool(payload.enable_entropy)
    if payload.enable_agent and universe.agent is None:
        cfg = AgentConfig(initial_budget=5000.0, action_probability=0.3)
        universe.agent = HashSphereAgent(universe.analyzer.state, config=cfg)
    if not payload.enable_agent:
        universe.agent = None
    return {
        "success": True,
        "state": _state_to_ui_dict(universe.analyzer.state, universe.analyzer),
        "nodes": len(universe.analyzer.state.nodes),
        "edges": len(universe.analyzer.state.edges),
        "agent_enabled": universe.agent is not None,
        "entropy_enabled": universe.entropy_enabled,
    }


@router.post("/load-platform-data")
async def api_load_platform_data(request: Request):
    universe = await get_user_universe(request)
    # Placeholder until real ingestion is wired.
    return {
        "success": False,
        "message": "Platform data ingestion not wired in this service build",
        "state": _state_to_ui_dict(universe.analyzer.state, universe.analyzer),
        "loaded": {},
        "total_nodes": len(universe.analyzer.state.nodes),
        "total_edges": len(universe.analyzer.state.edges),
    }


@router.post("/agent/spawn")
async def api_agent_spawn(request: Request, budget: float = 5000.0, action_probability: float = 0.3):
    universe = await get_user_universe(request)
    cfg = AgentConfig(initial_budget=float(budget), action_probability=float(action_probability))
    universe.agent = HashSphereAgent(universe.analyzer.state, config=cfg)
    return {"success": True, "agent": _agent_status(universe.agent)}


@router.post("/agent/step")
async def api_agent_step(request: Request):
    universe = await get_user_universe(request)
    if universe.agent is None:
        return {"success": False, "message": "No agent active"}
    action = universe.agent.step()
    return {"success": True, "status": _agent_status(universe.agent), "action": action}


@router.post("/agent/kill")
async def api_agent_kill(request: Request):
    universe = await get_user_universe(request)
    universe.agent = None
    return {"success": True}


@router.post("/agents/spawn")
async def api_agents_spawn(request: Request, count: int = 3, budget: float = 1000.0, action_probability: float = 0.3):
    universe = await get_user_universe(request)
    count_i = max(1, min(50, int(count)))
    spawned = 0
    for i in range(count_i):
        cfg = AgentConfig(
            dsid=f"agent_{datetime.utcnow().timestamp()}_{i}",
            name=f"Agent {i+1}",
            initial_budget=float(budget),
            action_probability=float(action_probability),
        )
        universe.agents.append(HashSphereAgent(universe.analyzer.state, config=cfg))
        spawned += 1
    return {"success": True, "spawned": spawned, "total_agents": len(universe.agents)}


@router.post("/agents/kill_all")
async def api_agents_kill_all(request: Request):
    universe = await get_user_universe(request)
    killed = len(universe.agents)
    universe.agents = []
    return {"success": True, "killed": killed}


@router.post("/experiment/setup")
async def api_experiment_setup(request: Request, experiment: str):
    universe = await get_user_universe(request)
    name = (experiment or "").strip().lower()
    if name == "zero_agent":
        universe.agent = None
        universe.agents = []
        universe.entropy_enabled = True
        return {
            "success": True,
            "experiment": "zero_agent",
            "description": "Disable agents; keep entropy enabled",
            "expected": "System remains symmetric longer; emergence less likely",
        }
    if name in {"stress_test", "long_run"}:
        universe.entropy_enabled = True
        if universe.agent is None:
            universe.agent = HashSphereAgent(universe.analyzer.state, config=AgentConfig(initial_budget=5000.0))
        return {
            "success": True,
            "experiment": name,
            "description": "Enable entropy + agent and run for many steps",
            "expected": "Asymmetry should rise and cores should form",
        }
    return {"success": False, "message": f"Unknown experiment: {experiment}"}


@router.post("/memory/cost")
async def api_memory_cost(request: Request, cost_multiplier: float = 1.0):
    universe = await get_user_universe(request)
    universe.memory_cost_multiplier = max(0.1, float(cost_multiplier))
    return {"success": True, "cost_multiplier": universe.memory_cost_multiplier}


@router.post("/metrics/record")
async def api_metrics_record(request: Request):
    universe = await get_user_universe(request)
    score, _ = _compute_asymmetry(universe)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "asymmetry_score": score,
        "nodes": len(universe.analyzer.state.nodes),
        "edges": len(universe.analyzer.state.edges),
        "entropy": universe.analyzer.state.entropy,
    }
    universe.metrics_history.append(record)
    return {"success": True, "record": record}


@router.get("/nodes")
async def api_nodes(request: Request):
    universe = await get_user_universe(request)
    return {"nodes": [n.to_dict() for n in universe.analyzer.state.nodes.values()]}


@router.get("/metrics")
async def api_metrics(request: Request):
    universe = await get_user_universe(request)
    state_dict = _state_to_ui_dict(universe.analyzer.state, universe.analyzer)
    return state_dict.get("metrics", {})


@router.post("/identity")
async def api_identity(request: Request, body: Dict[str, Any] = Body(...)):
    universe = await get_user_universe(request)
    dsid = body.get("dsid") or body.get("id") or body.get("name")
    if not dsid:
        raise HTTPException(status_code=400, detail="Missing dsid")

    node_type_str = (body.get("node_type") or body.get("type") or "user").lower()
    try:
        node_type = NodeType(node_type_str)
    except Exception:
        node_type = NodeType.USER

    initial_trust = float(body.get("trust", body.get("initial_trust", 0.5)))
    initial_value = float(body.get("value", body.get("initial_value", 0.0)))
    node = universe.analyzer.add_identity(
        str(dsid),
        node_type=node_type,
        initial_trust=max(0.0, min(1.0, initial_trust)),
        initial_value=max(0.0, initial_value),
    )
    return {"success": True, "node": node.to_dict()}
