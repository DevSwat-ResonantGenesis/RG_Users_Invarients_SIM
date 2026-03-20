"""
Hash Sphere Analyzer

Analyzes blockchain/crypto data and converts it to Hash Sphere graph structure.
Can ingest:
- Transaction data
- Wallet/address data
- Smart contract interactions
- Trust/reputation data
- Time-series state snapshots
"""

import hashlib
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .models import (
    HashNode, HashEdge, HashSphereState, 
    NodeType, EdgeType, NodeStatus, 
    Invariant, CORE_INVARIANTS
)


class HashSphereAnalyzer:
    """
    Analyzes and builds Hash Sphere graph from various data sources.
    """
    
    def __init__(self):
        self.state = HashSphereState()
        self.invariants = {inv.id: inv for inv in CORE_INVARIANTS}
        
    def generate_hash(self, data: Any) -> str:
        """Generate deterministic hash from data"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]
    
    def add_identity(
        self,
        dsid: str,
        node_type: NodeType = NodeType.USER,
        initial_trust: float = 0.5,
        initial_value: float = 0.0,
        metadata: Dict = None,
        skip_invariant_check: bool = True
    ) -> HashNode:
        """
        Add an identity to the Hash Sphere.
        Identity Layer: "who exists?"
        
        O(1) write path: skip_invariant_check=True (default) for fast writes.
        Set skip_invariant_check=False for audit/governance runs.
        """
        node_id = f"id_{self.generate_hash(dsid)}"
        
        # INVARIANT ENFORCEMENT: Ensure non-negative initial value
        initial_value = max(0.0, initial_value)
        
        node = HashNode(
            id=node_id,
            hash=self.generate_hash({"dsid": dsid, "type": node_type.value}),
            node_type=node_type,
            dsid=dsid,
            mass=1.0 + initial_value * 0.1,  # Value adds mass
            charge=initial_trust - 0.5,       # Trust determines charge
            temperature=1.0,
            trust_score=initial_trust,
            value=initial_value,
            status=NodeStatus.ACTIVE,
            metadata=metadata or {}
        )
        
        # Random initial position
        node.x = random.uniform(-100, 100)
        node.y = random.uniform(-100, 100)
        node.z = random.uniform(-100, 100)
        
        self.state.add_node(node)
        return node
    
    def add_state_snapshot(
        self,
        owner_dsid: str,
        state_data: Dict,
        cost: float = 0.0
    ) -> HashNode:
        """
        Add a state/memory snapshot to the Hash Sphere.
        State Layer: "what happened and what persists?"
        """
        state_hash = self.generate_hash(state_data)
        node_id = f"state_{state_hash}"
        
        # Find owner node
        owner_node = None
        for n in self.state.nodes.values():
            if n.dsid == owner_dsid:
                owner_node = n
                break
        
        node = HashNode(
            id=node_id,
            hash=state_hash,
            node_type=NodeType.STATE,
            owner=owner_dsid,
            mass=0.5 + len(json.dumps(state_data)) * 0.001,  # Size adds mass
            charge=0.0,
            temperature=1.0,
            cost_accumulated=cost,
            status=NodeStatus.ACTIVE,
            metadata={"state_data": state_data}
        )
        
        # Position near owner
        if owner_node:
            node.x = owner_node.x + random.uniform(-20, 20)
            node.y = owner_node.y + random.uniform(-20, 20)
            node.z = owner_node.z + random.uniform(-20, 20)
        else:
            node.x = random.uniform(-100, 100)
            node.y = random.uniform(-100, 100)
            node.z = random.uniform(-100, 100)
        
        self.state.add_node(node)
        
        # Create ownership edge
        if owner_node:
            edge = HashEdge(
                id=f"owns_{owner_node.id}_{node_id}",
                source=owner_node.id,
                target=node_id,
                edge_type=EdgeType.OWNS,
                weight=1.0,
                energy=cost
            )
            self.state.add_edge(edge)
        
        return node
    
    def add_transaction(
        self,
        from_dsid: str,
        to_dsid: str,
        amount: float,
        tx_type: EdgeType = EdgeType.TRANSFERS,
        block_number: int = None,
        proof_hash: str = None
    ) -> HashEdge:
        """
        Add a transaction to the Hash Sphere.
        Economic Layer: "what matters and what survives?"
        """
        # Find source and target nodes
        source_node = None
        target_node = None
        
        for n in self.state.nodes.values():
            if n.dsid == from_dsid:
                source_node = n
            if n.dsid == to_dsid:
                target_node = n
        
        if not source_node or not target_node:
            raise ValueError(f"Source or target identity not found")
        
        edge_id = f"tx_{self.generate_hash({'from': from_dsid, 'to': to_dsid, 'amount': amount, 'time': datetime.now().isoformat()})}"
        
        edge = HashEdge(
            id=edge_id,
            source=source_node.id,
            target=target_node.id,
            edge_type=tx_type,
            weight=amount,
            energy=amount * 0.01,  # Transaction cost
            block_number=block_number,
            proof_hash=proof_hash or self.generate_hash(edge_id),
            verified=proof_hash is not None
        )
        
        self.state.add_edge(edge)
        
        # Update node values with non-negative enforcement
        source_node.value -= amount
        # INVARIANT ENFORCEMENT: Prevent negative values, convert to debt
        if source_node.value < 0:
            source_node.cost_accumulated += abs(source_node.value)  # Track as debt
            source_node.value = 0.0
        target_node.value += amount
        
        # Update masses (value affects mass)
        source_node.mass = max(0.1, 1.0 + source_node.value * 0.1)
        target_node.mass = max(0.1, 1.0 + target_node.value * 0.1)
        
        # Increase temperature (activity)
        source_node.temperature = min(source_node.temperature + 0.5, 10.0)
        target_node.temperature = min(target_node.temperature + 0.5, 10.0)
        
        # Update trust based on successful transaction
        source_node.trust_score = min(1.0, source_node.trust_score + 0.01)
        target_node.trust_score = min(1.0, target_node.trust_score + 0.01)
        
        return edge
    
    def add_trust_relationship(
        self,
        from_dsid: str,
        to_dsid: str,
        trust_level: float  # -1 to 1
    ) -> HashEdge:
        """
        Add a trust relationship between identities.
        """
        source_node = None
        target_node = None
        
        for n in self.state.nodes.values():
            if n.dsid == from_dsid:
                source_node = n
            if n.dsid == to_dsid:
                target_node = n
        
        if not source_node or not target_node:
            raise ValueError(f"Source or target identity not found")
        
        edge_id = f"trust_{source_node.id}_{target_node.id}"
        
        edge = HashEdge(
            id=edge_id,
            source=source_node.id,
            target=target_node.id,
            edge_type=EdgeType.TRUSTS,
            weight=abs(trust_level),
            energy=0.0,
            metadata={"trust_level": trust_level}
        )
        
        self.state.add_edge(edge)
        
        # Update charges based on trust
        target_node.charge += trust_level * 0.1
        target_node.charge = max(-1.0, min(1.0, target_node.charge))
        
        return edge
    
    def check_invariants(self) -> List[Dict]:
        """
        Check all invariants and return violations.
        """
        violations = []
        
        for inv in self.invariants.values():
            inv.last_checked = datetime.now()
            
            # Check specific invariants
            if inv.id == "trust_bounds":
                for node in self.state.nodes.values():
                    if not (0 <= node.trust_score <= 1):
                        inv.violated = True
                        inv.violation_count += 1
                        violations.append({
                            "invariant": inv.name,
                            "node_id": node.id,
                            "message": f"Trust score {node.trust_score} out of bounds",
                            "severity": inv.severity
                        })
            
            elif inv.id == "non_negative_value":
                for node in self.state.nodes.values():
                    if node.value < 0:
                        inv.violated = True
                        inv.violation_count += 1
                        violations.append({
                            "invariant": inv.name,
                            "node_id": node.id,
                            "message": f"Negative value {node.value}",
                            "severity": inv.severity
                        })
            
            elif inv.id == "identity_uniqueness":
                dsids = [n.dsid for n in self.state.nodes.values() if n.dsid]
                if len(dsids) != len(set(dsids)):
                    inv.violated = True
                    inv.violation_count += 1
                    violations.append({
                        "invariant": inv.name,
                        "message": "Duplicate DSIDs detected",
                        "severity": inv.severity
                    })
        
        return violations
    
    def enforce_non_negative_values(self) -> int:
        """
        Fix existing negative values by converting to debt.
        Returns count of nodes fixed.
        """
        fixed_count = 0
        for node in self.state.nodes.values():
            if node.value < 0:
                node.cost_accumulated += abs(node.value)  # Track as debt
                node.value = 0.0
                fixed_count += 1
        return fixed_count
    
    def get_metrics(self, skip_invariant_check: bool = False) -> Dict:
        """Get current metrics of the Hash Sphere"""
        nodes = list(self.state.nodes.values())
        edges = list(self.state.edges.values())
        
        # Node type distribution
        type_dist = {}
        for node in nodes:
            t = node.node_type.value
            type_dist[t] = type_dist.get(t, 0) + 1
        
        # Status distribution
        status_dist = {}
        for node in nodes:
            s = node.status.value
            status_dist[s] = status_dist.get(s, 0) + 1
        
        # Edge type distribution
        edge_type_dist = {}
        for edge in edges:
            t = edge.edge_type.value
            edge_type_dist[t] = edge_type_dist.get(t, 0) + 1
        
        # Trust metrics
        trust_scores = [n.trust_score for n in nodes]
        avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0
        
        # Value metrics
        values = [n.value for n in nodes]
        total_value = sum(values)
        
        # Temperature metrics
        temps = [n.temperature for n in nodes]
        avg_temp = sum(temps) / len(temps) if temps else 0
        
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": type_dist,
            "node_status": status_dist,
            "edge_types": edge_type_dist,
            "total_mass": self.state.total_mass,
            "total_energy": self.state.total_energy,
            "entropy": self.state.compute_entropy(),
            "average_trust": avg_trust,
            "total_value": total_value,
            "average_temperature": avg_temp,
            "invariant_violations": 0 if skip_invariant_check else len(self.check_invariants())
        }
    
    def generate_demo_data(self, num_users: int = 20, num_transactions: int = 50) -> HashSphereState:
        """
        Generate demo data for visualization testing.
        Creates a realistic-looking Hash Sphere with:
        - Users with varying trust/value
        - Transactions between users
        - State snapshots
        - Trust relationships
        """
        # Create users
        users = []
        for i in range(num_users):
            is_whale = random.random() < 0.1  # 10% are whales
            is_trusted = random.random() < 0.3  # 30% are highly trusted
            
            user = self.add_identity(
                dsid=f"user_{i:04d}",
                node_type=NodeType.USER if random.random() > 0.2 else NodeType.AGENT,
                initial_trust=0.8 if is_trusted else random.uniform(0.3, 0.7),
                initial_value=random.uniform(1000, 10000) if is_whale else random.uniform(10, 500),
                metadata={"name": f"User {i}", "whale": is_whale, "trusted": is_trusted}
            )
            users.append(user)
        
        # Create some services/contracts
        for i in range(3):
            self.add_identity(
                dsid=f"service_{i}",
                node_type=NodeType.SERVICE,
                initial_trust=0.9,
                initial_value=random.uniform(5000, 20000),
                metadata={"name": f"Service {i}"}
            )
        
        # Create transactions
        for _ in range(num_transactions):
            from_user = random.choice(users)
            to_user = random.choice(users)
            
            if from_user.dsid != to_user.dsid and from_user.value > 10:
                amount = random.uniform(1, min(100, from_user.value * 0.1))
                try:
                    self.add_transaction(
                        from_dsid=from_user.dsid,
                        to_dsid=to_user.dsid,
                        amount=amount,
                        block_number=random.randint(1, 1000000)
                    )
                except:
                    pass
        
        # Create trust relationships
        for _ in range(num_users * 2):
            from_user = random.choice(users)
            to_user = random.choice(users)
            
            if from_user.dsid != to_user.dsid:
                trust_level = random.uniform(-0.5, 1.0)  # Mostly positive
                try:
                    self.add_trust_relationship(
                        from_dsid=from_user.dsid,
                        to_dsid=to_user.dsid,
                        trust_level=trust_level
                    )
                except:
                    pass
        
        # Create some state snapshots
        for user in random.sample(users, min(10, len(users))):
            self.add_state_snapshot(
                owner_dsid=user.dsid,
                state_data={"balance": user.value, "timestamp": datetime.now().isoformat()},
                cost=random.uniform(0.01, 0.1)
            )
        
        return self.state
    
    def to_visualization_format(self) -> Dict:
        """
        Convert state to format suitable for 3D visualization.
        """
        return {
            "nodes": [n.to_dict() for n in self.state.nodes.values()],
            "edges": [e.to_dict() for e in self.state.edges.values()],
            "metrics": self.get_metrics(),
            "invariants": [inv.to_dict() for inv in self.invariants.values()],
            "violations": self.check_invariants()
        }
