"""User Data Loader for State Physics Service.

Loads real user data from blockchain and memory services instead of demo data.
This ensures each user sees their own isolated simulation based on their actual
blockchain activity, identities, and transactions.

Author: Agent 7 - ResonantGenesis Team
Created: February 22, 2026
"""

import httpx
import os
from typing import Dict, List, Any, Optional
from .analyzer import HashSphereAnalyzer
from .models import HashSphereState, NodeType


# Service URLs - configurable via environment
BLOCKCHAIN_SERVICE_URL = os.getenv("BLOCKCHAIN_SERVICE_URL", "http://blockchain_service:8000")
MEMORY_SERVICE_URL = os.getenv("MEMORY_SERVICE_URL", "http://memory_service:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")


async def fetch_user_identities(user_id: str, org_id: str = "") -> List[Dict[str, Any]]:
    """Fetch user's blockchain identities (DSIDs) from blockchain service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-user-id": user_id}
            if org_id:
                headers["x-org-id"] = org_id
            
            # Try to get user's registered identities
            resp = await client.get(
                f"{BLOCKCHAIN_SERVICE_URL}/api/v1/identities",
                headers=headers
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("identities", [])
            
            return []
    except Exception as e:
        print(f"Error fetching identities for user {user_id}: {e}")
        return []


async def fetch_user_transactions(user_id: str, org_id: str = "", limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch user's transactions from blockchain service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-user-id": user_id}
            if org_id:
                headers["x-org-id"] = org_id
            
            resp = await client.get(
                f"{BLOCKCHAIN_SERVICE_URL}/api/v1/transactions",
                headers=headers,
                params={"limit": limit}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("transactions", [])
            
            return []
    except Exception as e:
        print(f"Error fetching transactions for user {user_id}: {e}")
        return []


async def fetch_user_memories(user_id: str, org_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch user's memory entries from memory service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-user-id": user_id}
            if org_id:
                headers["x-org-id"] = org_id
            
            resp = await client.get(
                f"{MEMORY_SERVICE_URL}/api/v1/memories",
                headers=headers,
                params={"limit": limit}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("memories", [])
            
            return []
    except Exception as e:
        print(f"Error fetching memories for user {user_id}: {e}")
        return []


async def fetch_user_agents(user_id: str, org_id: str = "") -> List[Dict[str, Any]]:
    """Fetch user's AI agents from relevant service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-user-id": user_id}
            if org_id:
                headers["x-org-id"] = org_id
            
            # Try agent engine service
            resp = await client.get(
                f"http://agent_engine_service:8000/api/v1/agents",
                headers=headers
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("agents", [])
            
            return []
    except Exception as e:
        print(f"Error fetching agents for user {user_id}: {e}")
        return []


def build_universe_from_user_data(
    analyzer: HashSphereAnalyzer,
    user_id: str,
    identities: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    memories: List[Dict[str, Any]],
    agents: List[Dict[str, Any]]
) -> HashSphereState:
    """
    Build a Hash Sphere state from real user data.
    
    This creates a universe that reflects the user's actual:
    - Blockchain identities (DSIDs)
    - Transaction history
    - Memory entries
    - AI agents
    """
    # Reset state
    analyzer.state = HashSphereState()
    
    # Add the user's own identity as the central node
    user_node = analyzer.add_identity(
        dsid=f"user:{user_id}",
        node_type=NodeType.USER,
        initial_trust=0.5,
        initial_value=100.0,
        metadata={"user_id": user_id, "is_owner": True}
    )
    
    # Add user's blockchain identities
    dsid_map = {f"user:{user_id}": user_node}
    
    for identity in identities:
        dsid = identity.get("dsid") or identity.get("id")
        if dsid and dsid not in dsid_map:
            node = analyzer.add_identity(
                dsid=dsid,
                node_type=NodeType.USER,
                initial_trust=identity.get("trust_score", 0.5),
                initial_value=identity.get("value", 50.0),
                metadata=identity.get("metadata", {})
            )
            dsid_map[dsid] = node
    
    # Add user's AI agents
    for agent in agents:
        agent_id = agent.get("id") or agent.get("agent_id")
        if agent_id:
            agent_dsid = f"agent:{agent_id}"
            if agent_dsid not in dsid_map:
                node = analyzer.add_identity(
                    dsid=agent_dsid,
                    node_type=NodeType.AGENT,
                    initial_trust=agent.get("trust_score", 0.6),
                    initial_value=agent.get("credits", 100.0),
                    metadata={
                        "name": agent.get("name", "Unknown Agent"),
                        "status": agent.get("status", "active")
                    }
                )
                dsid_map[agent_dsid] = node
    
    # Add transactions as edges
    for tx in transactions:
        from_dsid = tx.get("from_dsid") or tx.get("from_address")
        to_dsid = tx.get("to_dsid") or tx.get("to_address")
        amount = tx.get("amount", 1.0)
        
        # Ensure both nodes exist
        if from_dsid and from_dsid not in dsid_map:
            node = analyzer.add_identity(
                dsid=from_dsid,
                node_type=NodeType.USER,
                initial_trust=0.4,
                initial_value=50.0
            )
            dsid_map[from_dsid] = node
        
        if to_dsid and to_dsid not in dsid_map:
            node = analyzer.add_identity(
                dsid=to_dsid,
                node_type=NodeType.USER,
                initial_trust=0.4,
                initial_value=50.0
            )
            dsid_map[to_dsid] = node
        
        # Add transaction edge
        if from_dsid and to_dsid and from_dsid != to_dsid:
            try:
                analyzer.add_transaction(
                    from_dsid=from_dsid,
                    to_dsid=to_dsid,
                    amount=float(amount),
                    block_number=tx.get("block_number", 0)
                )
            except Exception:
                pass
    
    # Add memory entries as state snapshots
    for memory in memories:
        owner_dsid = memory.get("owner_dsid") or f"user:{user_id}"
        if owner_dsid in dsid_map:
            try:
                analyzer.add_state_snapshot(
                    owner_dsid=owner_dsid,
                    state_data=memory.get("content", {}),
                    cost=memory.get("cost", 0.01)
                )
            except Exception:
                pass
    
    # Compute entropy
    analyzer.state.entropy = analyzer.state.compute_entropy()
    
    return analyzer.state


async def load_user_universe(
    analyzer: HashSphereAnalyzer,
    user_id: str,
    org_id: str = ""
) -> HashSphereState:
    """
    Load a complete universe for a specific user.
    
    This fetches all relevant data from backend services and builds
    a personalized Hash Sphere state for the user.
    """
    # Fetch all user data in parallel
    identities = await fetch_user_identities(user_id, org_id)
    transactions = await fetch_user_transactions(user_id, org_id)
    memories = await fetch_user_memories(user_id, org_id)
    agents = await fetch_user_agents(user_id, org_id)
    
    # Build universe from real data
    state = build_universe_from_user_data(
        analyzer=analyzer,
        user_id=user_id,
        identities=identities,
        transactions=transactions,
        memories=memories,
        agents=agents
    )
    
    return state


def create_empty_universe_for_new_user(
    analyzer: HashSphereAnalyzer,
    user_id: str
) -> HashSphereState:
    """
    Create an empty universe for a new user with no data.
    
    This is used when a user has no blockchain activity yet.
    Shows them an empty simulation they can populate.
    """
    analyzer.state = HashSphereState()
    
    # Add just the user's own node
    analyzer.add_identity(
        dsid=f"user:{user_id}",
        node_type=NodeType.USER,
        initial_trust=0.5,
        initial_value=100.0,
        metadata={"user_id": user_id, "is_owner": True, "is_new": True}
    )
    
    # Add a welcome service node
    analyzer.add_identity(
        dsid="system:welcome",
        node_type=NodeType.SERVICE,
        initial_trust=1.0,
        initial_value=0.0,
        metadata={"name": "Welcome to ResonantGenesis", "system": True}
    )
    
    analyzer.state.entropy = analyzer.state.compute_entropy()
    
    return analyzer.state
