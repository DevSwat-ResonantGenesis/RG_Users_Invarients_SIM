"""
Hash Sphere Data Models

Three coupled layers:
1. Identity Layer (DSID) - "who exists?"
2. State/Memory Layer - "what happened and what persists?"
3. Economic/Temporal Layer - "what matters and what survives?"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from datetime import datetime
import hashlib
import json


class NodeType(Enum):
    """Types of nodes in Hash Sphere"""
    # Identity Layer
    USER = "user"
    AGENT = "agent"
    SERVICE = "service"
    CONTRACT = "contract"
    
    # State/Memory Layer
    STATE = "state"
    MEMORY = "memory"
    PROOF = "proof"
    ANCHOR = "anchor"
    
    # Economic Layer
    TRANSACTION = "transaction"
    WALLET = "wallet"
    ASSET = "asset"


class EdgeType(Enum):
    """Types of edges (interactions) in Hash Sphere"""
    # Identity relationships
    OWNS = "owns"
    DELEGATES = "delegates"
    TRUSTS = "trusts"
    
    # State relationships
    DERIVES = "derives"
    PROVES = "proves"
    REFERENCES = "references"
    
    # Economic relationships
    TRANSFERS = "transfers"
    PAYS = "pays"
    STAKES = "stakes"


class NodeStatus(Enum):
    """Health/activity status of nodes"""
    ACTIVE = "active"          # Recently active, high trust
    STABLE = "stable"          # Consistent over time
    COOLING = "cooling"        # Decreasing activity
    COLD = "cold"              # Inactive, low influence
    DECAYING = "decaying"      # Losing trust/mass
    COLLAPSED = "collapsed"    # Failed/violated constraints


@dataclass
class HashNode:
    """
    A node in the Hash Sphere universe.
    
    Maps to physics:
    - hash = particle state
    - mass = economic weight (accumulated value/trust)
    - charge = identity polarity (trust direction)
    - temperature = activity level
    """
    id: str
    hash: str
    node_type: NodeType
    
    # Identity properties
    owner: Optional[str] = None
    dsid: Optional[str] = None  # Decentralized Secure ID
    
    # Physical properties (for force simulation)
    mass: float = 1.0           # Economic weight
    charge: float = 0.0         # Trust polarity (-1 to 1)
    temperature: float = 1.0    # Activity level (0 to infinity)
    
    # Position in 3D space (computed by physics engine)
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    # Velocity (for simulation)
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    
    # State properties
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    mutation_count: int = 0
    
    # Economic properties
    value: float = 0.0          # Stored value
    cost_accumulated: float = 0.0  # Total cost paid
    trust_score: float = 0.5    # 0 to 1
    
    # Status
    status: NodeStatus = NodeStatus.ACTIVE
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "hash": self.hash,
            "type": self.node_type.value,
            "owner": self.owner,
            "dsid": self.dsid,
            "mass": self.mass,
            "charge": self.charge,
            "temperature": self.temperature,
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "velocity": {"vx": self.vx, "vy": self.vy, "vz": self.vz},
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "access_count": self.access_count,
            "mutation_count": self.mutation_count,
            "value": self.value,
            "cost_accumulated": self.cost_accumulated,
            "trust_score": self.trust_score,
            "status": self.status.value,
            "metadata": self.metadata
        }


@dataclass
class HashEdge:
    """
    An edge (interaction) in the Hash Sphere universe.
    
    Maps to physics:
    - weight = interaction strength
    - energy = cost of interaction
    - direction = causality flow
    """
    id: str
    source: str
    target: str
    edge_type: EdgeType
    
    # Physical properties
    weight: float = 1.0         # Interaction strength
    energy: float = 0.0         # Cost/energy of this interaction
    
    # Temporal properties
    timestamp: datetime = field(default_factory=datetime.now)
    block_number: Optional[int] = None
    
    # Proof properties
    proof_hash: Optional[str] = None
    verified: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "weight": self.weight,
            "energy": self.energy,
            "timestamp": self.timestamp.isoformat(),
            "block_number": self.block_number,
            "proof_hash": self.proof_hash,
            "verified": self.verified,
            "metadata": self.metadata
        }


@dataclass
class HashSphereState:
    """
    Complete state of the Hash Sphere universe at a point in time.
    """
    nodes: Dict[str, HashNode] = field(default_factory=dict)
    edges: Dict[str, HashEdge] = field(default_factory=dict)
    
    # Global metrics
    total_mass: float = 0.0
    total_energy: float = 0.0
    entropy: float = 0.0
    temperature: float = 1.0
    
    # Time
    block_height: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_node(self, node: HashNode):
        self.nodes[node.id] = node
        self.total_mass += node.mass
        
    def add_edge(self, edge: HashEdge):
        self.edges[edge.id] = edge
        self.total_energy += edge.energy
        
    def get_node(self, node_id: str) -> Optional[HashNode]:
        return self.nodes.get(node_id)
    
    def get_edges_from(self, node_id: str) -> List[HashEdge]:
        return [e for e in self.edges.values() if e.source == node_id]
    
    def get_edges_to(self, node_id: str) -> List[HashEdge]:
        return [e for e in self.edges.values() if e.target == node_id]
    
    def compute_entropy(self) -> float:
        """
        Compute entropy of the system.
        Higher entropy = more distributed, less concentrated.
        """
        if not self.nodes:
            return 0.0
        
        total_value = sum(n.value for n in self.nodes.values())
        if total_value == 0:
            return 0.0
        
        entropy = 0.0
        for node in self.nodes.values():
            if node.value > 0:
                p = node.value / total_value
                entropy -= p * (p if p > 0 else 1)
        
        return entropy
    
    def to_dict(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "metrics": {
                "total_mass": self.total_mass,
                "total_energy": self.total_energy,
                "entropy": self.entropy,
                "temperature": self.temperature,
                "node_count": len(self.nodes),
                "edge_count": len(self.edges)
            },
            "time": {
                "block_height": self.block_height,
                "timestamp": self.timestamp.isoformat()
            }
        }


@dataclass
class Invariant:
    """
    A conservation law / constraint in Hash Sphere.
    Violations cause visible instability.
    """
    id: str
    name: str
    description: str
    
    # The check function (as string for serialization)
    check_expression: str
    
    # Severity
    severity: str = "critical"  # critical, high, medium, low
    
    # Status
    violated: bool = False
    last_checked: datetime = field(default_factory=datetime.now)
    violation_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "violated": self.violated,
            "last_checked": self.last_checked.isoformat(),
            "violation_count": self.violation_count
        }


# Built-in invariants (conservation laws)
CORE_INVARIANTS = [
    Invariant(
        id="mass_conservation",
        name="Mass Conservation",
        description="Total mass cannot be created or destroyed, only transferred",
        check_expression="sum(node.mass for node in nodes) == initial_mass",
        severity="critical"
    ),
    Invariant(
        id="energy_conservation",
        name="Energy Conservation",
        description="Total energy is conserved across transactions",
        check_expression="sum(edge.energy for edge in edges) <= total_energy_budget",
        severity="critical"
    ),
    Invariant(
        id="identity_uniqueness",
        name="Identity Uniqueness",
        description="Each DSID maps to exactly one entity",
        check_expression="len(set(node.dsid for node in nodes if node.dsid)) == len([n for n in nodes if n.dsid])",
        severity="critical"
    ),
    Invariant(
        id="causality",
        name="Causality",
        description="Effects cannot precede causes (no backward edges in time)",
        check_expression="all(edge.timestamp >= nodes[edge.source].created_at for edge in edges)",
        severity="critical"
    ),
    Invariant(
        id="trust_bounds",
        name="Trust Bounds",
        description="Trust scores must remain in [0, 1]",
        check_expression="all(0 <= node.trust_score <= 1 for node in nodes)",
        severity="high"
    ),
    Invariant(
        id="non_negative_value",
        name="Non-Negative Value",
        description="No node can have negative value",
        check_expression="all(node.value >= 0 for node in nodes)",
        severity="critical"
    )
]
