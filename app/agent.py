"""
Hash Sphere Minimum Viable Agent

A single agent that:
- Has a budget
- Pays to store state (memory cost)
- Gains trust slowly through activity
- Loses trust if idle
- Makes economic decisions
- Creates asymmetry through intent

This is NOT a swarm. This is ONE agent.
One agent is enough to break symmetry and enable evolution.
"""

import random
import math
from datetime import datetime
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from .models import HashNode, HashEdge, HashSphereState, NodeType, EdgeType, NodeStatus

# CRITICAL: Import sandbox for secure code execution
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ed_service.sandbox import SandboxExecutor, SandboxConfig
    SANDBOX_AVAILABLE = True
except ImportError:
    SANDBOX_AVAILABLE = False
    logging.warning("Sandbox not available - agents will run without isolation!")

@dataclass
class AgentConfig:
    """Configuration for the minimum viable agent"""
    # Identity
    dsid: str = "agent_prime"
    name: str = "Prime Agent"
    
    # Budget
    initial_budget: float = 1000.0
    income_per_step: float = 1.0          # Passive income
    
    # Costs
    memory_cost_per_unit: float = 0.01    # Cost to store state
    transaction_cost: float = 0.1         # Cost per transaction
    existence_cost: float = 0.05          # Cost just to exist
    
    # Trust dynamics
    trust_gain_per_action: float = 0.002  # Trust gained from activity
    trust_decay_per_idle: float = 0.005   # Trust lost when idle
    max_trust: float = 0.95
    min_trust: float = 0.1
    
    # Behavior
    action_probability: float = 0.3       # Chance to act each step
    memory_probability: float = 0.1       # Chance to store memory
    transaction_probability: float = 0.2  # Chance to transact
    
    # Strategy
    prefer_trusted: bool = True           # Prefer transacting with trusted nodes
    prefer_wealthy: bool = True           # Prefer transacting with wealthy nodes
    risk_tolerance: float = 0.5           # 0 = conservative, 1 = aggressive


@dataclass
class AgentMemory:
    """Agent's memory of past interactions"""
    interactions: List[Dict] = field(default_factory=list)
    trusted_nodes: Dict[str, float] = field(default_factory=dict)
    total_spent: float = 0.0
    total_earned: float = 0.0
    successful_transactions: int = 0
    failed_transactions: int = 0


class HashSphereAgent:
    """
    Minimum Viable Agent for Hash Sphere.
    
    This agent:
    1. Exists in the universe (has a node)
    2. Has economic constraints (budget, costs)
    3. Makes decisions (transact, store, idle)
    4. Builds reputation (trust dynamics)
    5. Creates asymmetry (breaks equilibrium)
    
    One agent is sufficient to:
    - Create uneven growth
    - Form trust gradients
    - Cause resource clustering
    - Generate cold regions
    """
    
    def __init__(self, state: HashSphereState, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.state = state
        self.memory = AgentMemory()
        self.node: Optional[HashNode] = None
        self.step_count = 0
        self.idle_steps = 0
        self.last_action = None
        
        # Create agent node in the universe
        self._create_agent_node()
    
    def _create_agent_node(self):
        """Create the agent's node in Hash Sphere"""
        import hashlib
        
        node_id = f"agent_{hashlib.sha256(self.config.dsid.encode()).hexdigest()[:12]}"
        
        self.node = HashNode(
            id=node_id,
            hash=hashlib.sha256(f"{self.config.dsid}_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            node_type=NodeType.AGENT,
            dsid=self.config.dsid,
            mass=1.0 + self.config.initial_budget * 0.01,
            charge=0.0,  # Neutral initially
            temperature=1.0,
            trust_score=0.5,
            value=self.config.initial_budget,
            status=NodeStatus.ACTIVE,
            metadata={
                "name": self.config.name,
                "type": "autonomous_agent",
                "created": datetime.now().isoformat()
            }
        )
        
        # Position at center initially (will be pushed by physics)
        self.node.x = random.uniform(-50, 50)
        self.node.y = random.uniform(-50, 50)
        self.node.z = random.uniform(-50, 50)
        
        self.state.add_node(self.node)
    
    def step(self) -> Dict:
        """
        Execute one step of agent behavior.
        Returns action taken and results.
        """
        self.step_count += 1
        action_result = {"step": self.step_count, "action": "idle", "details": {}}
        
        # 1. Pay existence cost
        self._pay_existence_cost()
        
        # 2. Receive income
        self._receive_income()
        
        # 3. Decide whether to act
        if random.random() < self.config.action_probability:
            # Choose action
            action = self._choose_action()
            
            if action == "transact":
                action_result = self._execute_transaction()
            elif action == "store_memory":
                action_result = self._store_memory()
            elif action == "build_trust":
                action_result = self._build_trust()
            
            self.idle_steps = 0
            self._gain_trust()
        else:
            self.idle_steps += 1
            self._decay_trust()
            action_result["action"] = "idle"
            action_result["details"] = {"idle_steps": self.idle_steps}
        
        # 4. Update node state
        self._update_node_state()
        
        self.last_action = action_result
        return action_result
    
    def _pay_existence_cost(self):
        """Pay the cost of existing"""
        if self.node.value >= self.config.existence_cost:
            self.node.value -= self.config.existence_cost
            self.memory.total_spent += self.config.existence_cost
    
    def _receive_income(self):
        """Receive passive income"""
        self.node.value += self.config.income_per_step
        self.memory.total_earned += self.config.income_per_step
    
    def _choose_action(self) -> str:
        """Choose which action to take"""
        actions = []
        
        # Can we afford to transact?
        if self.node.value > self.config.transaction_cost * 10:
            actions.append("transact")
        
        # Should we store memory?
        if random.random() < self.config.memory_probability:
            actions.append("store_memory")
        
        # Should we build trust?
        if self.node.trust_score < 0.7:
            actions.append("build_trust")
        
        if not actions:
            return "idle"
        
        return random.choice(actions)
    
    def _execute_transaction(self) -> Dict:
        """Execute a transaction with another node"""
        # Find potential targets
        targets = [n for n in self.state.nodes.values() 
                   if n.id != self.node.id and n.node_type in [NodeType.USER, NodeType.SERVICE]]
        
        if not targets:
            return {"step": self.step_count, "action": "transact", "success": False, "reason": "no_targets"}
        
        # Select target based on strategy
        target = self._select_transaction_target(targets)
        
        # Determine amount (risk-adjusted)
        max_amount = self.node.value * 0.1 * self.config.risk_tolerance
        amount = random.uniform(1, max(1, max_amount))
        
        if amount > self.node.value - self.config.transaction_cost:
            return {"step": self.step_count, "action": "transact", "success": False, "reason": "insufficient_funds"}
        
        # Execute transaction
        self.node.value -= amount + self.config.transaction_cost
        target.value += amount
        
        # Update masses
        self.node.mass = max(0.1, 1.0 + self.node.value * 0.01)
        target.mass = max(0.1, 1.0 + target.value * 0.01)
        
        # Increase temperatures
        self.node.temperature = min(self.node.temperature + 0.3, 5.0)
        target.temperature = min(target.temperature + 0.2, 5.0)
        
        # Create edge
        import hashlib
        edge_id = f"tx_{hashlib.sha256(f'{self.node.id}_{target.id}_{self.step_count}'.encode()).hexdigest()[:12]}"
        
        edge = HashEdge(
            id=edge_id,
            source=self.node.id,
            target=target.id,
            edge_type=EdgeType.TRANSFERS,
            weight=amount,
            energy=self.config.transaction_cost,
            metadata={"agent_initiated": True, "step": self.step_count}
        )
        self.state.add_edge(edge)
        
        # Update memory
        self.memory.total_spent += amount + self.config.transaction_cost
        self.memory.successful_transactions += 1
        self.memory.interactions.append({
            "type": "transaction",
            "target": target.dsid,
            "amount": amount,
            "step": self.step_count
        })
        
        # Update trust relationship
        if target.dsid:
            current_trust = self.memory.trusted_nodes.get(target.dsid, 0.5)
            self.memory.trusted_nodes[target.dsid] = min(1.0, current_trust + 0.05)
        
        return {
            "step": self.step_count,
            "action": "transact",
            "success": True,
            "target": target.dsid,
            "amount": amount,
            "cost": self.config.transaction_cost
        }
    
    def _select_transaction_target(self, targets: List[HashNode]) -> HashNode:
        """Select a transaction target based on strategy"""
        if not targets:
            return None
        
        # Score each target
        scores = []
        for target in targets:
            score = 1.0
            
            if self.config.prefer_trusted:
                score *= (1 + target.trust_score)
            
            if self.config.prefer_wealthy:
                score *= (1 + math.log1p(target.value) * 0.1)
            
            # Prefer nodes we've interacted with before
            if target.dsid in self.memory.trusted_nodes:
                score *= (1 + self.memory.trusted_nodes[target.dsid])
            
            scores.append(score)
        
        # Weighted random selection
        total = sum(scores)
        if total == 0:
            return random.choice(targets)
        
        r = random.uniform(0, total)
        cumulative = 0
        for target, score in zip(targets, scores):
            cumulative += score
            if r <= cumulative:
                return target
        
        return targets[-1]
    
    def _store_memory(self) -> Dict:
        """Store a memory snapshot (costs money)"""
        import hashlib
        import json
        
        # Calculate cost based on memory size
        memory_data = {
            "step": self.step_count,
            "value": self.node.value,
            "trust": self.node.trust_score,
            "interactions": len(self.memory.interactions),
            "timestamp": datetime.now().isoformat()
        }
        
        cost = len(json.dumps(memory_data)) * self.config.memory_cost_per_unit
        
        if cost > self.node.value:
            return {"step": self.step_count, "action": "store_memory", "success": False, "reason": "insufficient_funds"}
        
        # Pay cost
        self.node.value -= cost
        self.memory.total_spent += cost
        
        # Create state node
        state_hash = hashlib.sha256(json.dumps(memory_data, sort_keys=True).encode()).hexdigest()[:16]
        state_id = f"state_{state_hash}"
        
        state_node = HashNode(
            id=state_id,
            hash=state_hash,
            node_type=NodeType.STATE,
            owner=self.config.dsid,
            mass=0.3,
            charge=0.0,
            temperature=0.5,
            cost_accumulated=cost,
            status=NodeStatus.ACTIVE,
            metadata={"memory_data": memory_data}
        )
        
        # Position near agent
        state_node.x = self.node.x + random.uniform(-10, 10)
        state_node.y = self.node.y + random.uniform(-10, 10)
        state_node.z = self.node.z + random.uniform(-10, 10)
        
        self.state.add_node(state_node)
        
        # Create ownership edge
        edge = HashEdge(
            id=f"owns_{self.node.id}_{state_id}",
            source=self.node.id,
            target=state_id,
            edge_type=EdgeType.OWNS,
            weight=1.0,
            energy=cost
        )
        self.state.add_edge(edge)
        
        return {
            "step": self.step_count,
            "action": "store_memory",
            "success": True,
            "cost": cost,
            "state_id": state_id
        }
    
    def _build_trust(self) -> Dict:
        """Actively build trust with other nodes"""
        # Find nodes to trust
        targets = [n for n in self.state.nodes.values() 
                   if n.id != self.node.id and n.trust_score > 0.3]
        
        if not targets:
            return {"step": self.step_count, "action": "build_trust", "success": False, "reason": "no_targets"}
        
        # Select a target (prefer already-trusted)
        target = max(targets, key=lambda n: n.trust_score)
        
        # Create trust edge
        import hashlib
        edge_id = f"trust_{hashlib.sha256(f'{self.node.id}_{target.id}_{self.step_count}'.encode()).hexdigest()[:12]}"
        
        edge = HashEdge(
            id=edge_id,
            source=self.node.id,
            target=target.id,
            edge_type=EdgeType.TRUSTS,
            weight=0.5,
            energy=0.0,
            metadata={"agent_initiated": True}
        )
        self.state.add_edge(edge)
        
        # Boost target's trust slightly
        target.trust_score = min(1.0, target.trust_score + 0.01)
        target.charge = target.trust_score - 0.5
        
        return {
            "step": self.step_count,
            "action": "build_trust",
            "success": True,
            "target": target.dsid
        }
    
    def _gain_trust(self):
        """Gain trust from activity"""
        self.node.trust_score = min(
            self.config.max_trust,
            self.node.trust_score + self.config.trust_gain_per_action
        )
        self.node.charge = self.node.trust_score - 0.5
    
    def _decay_trust(self):
        """Lose trust from idleness"""
        self.node.trust_score = max(
            self.config.min_trust,
            self.node.trust_score - self.config.trust_decay_per_idle
        )
        self.node.charge = self.node.trust_score - 0.5
    
    def _update_node_state(self):
        """Update the agent's node state"""
        # Update mass based on value
        self.node.mass = max(0.1, 1.0 + self.node.value * 0.01)
        
        # Update temperature (decays naturally)
        self.node.temperature = max(0.1, self.node.temperature * 0.95)
        
        # Update status
        if self.node.temperature > 0.5:
            self.node.status = NodeStatus.ACTIVE
        elif self.node.temperature > 0.2:
            self.node.status = NodeStatus.STABLE
        else:
            self.node.status = NodeStatus.COOLING
        
        # Check for collapse (out of money)
        if self.node.value <= 0:
            self.node.status = NodeStatus.COLLAPSED
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "dsid": self.config.dsid,
            "name": self.config.name,
            "step": self.step_count,
            "value": self.node.value,
            "trust": self.node.trust_score,
            "temperature": self.node.temperature,
            "status": self.node.status.value,
            "idle_steps": self.idle_steps,
            "total_spent": self.memory.total_spent,
            "total_earned": self.memory.total_earned,
            "successful_transactions": self.memory.successful_transactions,
            "interactions": len(self.memory.interactions),
            "last_action": self.last_action
        }
