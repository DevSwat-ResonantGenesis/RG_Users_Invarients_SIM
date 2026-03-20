"""
Hash Sphere Entropy System

Introduces:
- Random perturbations (thermal noise)
- Time-based decay (trust, value, temperature)
- Trust noise (reputation fluctuation)
- Activity injection (keeps system alive)

Target: Temperature ~0.2-0.4 for emergence
"""

import random
import math
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from .models import HashNode, HashEdge, HashSphereState, NodeStatus, NodeType


@dataclass
class EntropyConfig:
    """Configuration for entropy injection"""
    # Perturbation
    position_noise: float = 0.5          # Random position jitter
    velocity_noise: float = 0.1          # Random velocity jitter
    
    # Decay rates (per step)
    trust_decay: float = 0.001           # Trust decays slowly
    value_decay: float = 0.0001          # Value decays very slowly (storage cost)
    temperature_floor: float = 0.05      # Minimum temperature (never fully cold)
    
    # Trust noise
    trust_noise: float = 0.01            # Random trust fluctuation
    
    # Activity injection
    activity_probability: float = 0.02   # Chance of random activity per node per step
    activity_boost: float = 0.3          # Temperature boost from activity
    
    # Asymmetry seeds
    wealth_concentration: float = 0.1    # Probability of wealth transfer to whales
    trust_gradient: float = 0.05         # Probability of trust flowing to trusted nodes


class EntropyEngine:
    """
    Injects entropy into Hash Sphere to enable emergence.
    
    Without entropy:
    - System freezes into static equilibrium
    - No evolution, no competition, no structure
    
    With entropy:
    - Continuous perturbation prevents lock-in
    - Decay creates pressure to act
    - Noise enables exploration
    - Asymmetry seeds structure formation
    """
    
    def __init__(self, config: EntropyConfig = None):
        self.config = config or EntropyConfig()
        self.step_count = 0
        
    def inject_entropy(self, state: HashSphereState) -> HashSphereState:
        """
        Inject entropy into the system.
        Call this each simulation step.
        """
        self.step_count += 1
        
        nodes = list(state.nodes.values())
        
        for node in nodes:
            # 1. Position perturbation (thermal noise)
            node.x += random.gauss(0, self.config.position_noise)
            node.y += random.gauss(0, self.config.position_noise)
            node.z += random.gauss(0, self.config.position_noise)
            
            # 2. Velocity perturbation
            node.vx += random.gauss(0, self.config.velocity_noise)
            node.vy += random.gauss(0, self.config.velocity_noise)
            node.vz += random.gauss(0, self.config.velocity_noise)
            
            # 3. Trust decay (reputation fades without reinforcement)
            if node.trust_score > 0.1:
                node.trust_score -= self.config.trust_decay
                node.trust_score = max(0.1, node.trust_score)
            
            # 4. Trust noise (reputation fluctuates)
            noise = random.gauss(0, self.config.trust_noise)
            node.trust_score += noise
            node.trust_score = max(0.0, min(1.0, node.trust_score))
            
            # 5. Value decay (storage cost)
            if node.value > 0:
                decay = node.value * self.config.value_decay
                node.value -= decay
                node.cost_accumulated += decay
            
            # 6. Temperature floor (never fully dead)
            if node.temperature < self.config.temperature_floor:
                node.temperature = self.config.temperature_floor
            
            # 7. Random activity injection
            if random.random() < self.config.activity_probability:
                node.temperature += self.config.activity_boost
                node.access_count += 1
                if node.status in [NodeStatus.COLD, NodeStatus.COOLING]:
                    node.status = NodeStatus.ACTIVE
            
            # 8. Update charge based on trust
            node.charge = node.trust_score - 0.5
        
        # 9. Asymmetry seeding - wealth concentration
        self._seed_wealth_asymmetry(state)
        
        # 10. Asymmetry seeding - trust gradients
        self._seed_trust_asymmetry(state)
        
        # Update global temperature
        temps = [n.temperature for n in state.nodes.values()]
        state.temperature = sum(temps) / len(temps) if temps else 0
        
        return state
    
    def _seed_wealth_asymmetry(self, state: HashSphereState):
        """
        Occasionally transfer small amounts to high-value nodes.
        Creates wealth concentration over time.
        """
        if random.random() > self.config.wealth_concentration:
            return
        
        nodes = list(state.nodes.values())
        if len(nodes) < 2:
            return
        
        # Find a whale (high value node)
        sorted_by_value = sorted(nodes, key=lambda n: n.value, reverse=True)
        whale = sorted_by_value[0]
        
        # Find a random non-whale with value
        donors = [n for n in nodes if n.value > 1 and n.id != whale.id]
        if not donors:
            return
        
        donor = random.choice(donors)
        
        # Small transfer (simulates economic gravity)
        amount = min(0.1, donor.value * 0.001)
        donor.value -= amount
        whale.value += amount
        
        # Update masses
        donor.mass = max(0.1, 1.0 + donor.value * 0.1)
        whale.mass = max(0.1, 1.0 + whale.value * 0.1)
    
    def _seed_trust_asymmetry(self, state: HashSphereState):
        """
        Occasionally boost trust of already-trusted nodes.
        Creates trust gradients and hierarchy.
        """
        if random.random() > self.config.trust_gradient:
            return
        
        nodes = list(state.nodes.values())
        if len(nodes) < 2:
            return
        
        # Find highly trusted node
        sorted_by_trust = sorted(nodes, key=lambda n: n.trust_score, reverse=True)
        trusted = sorted_by_trust[0]
        
        # Small trust boost (reputation compounds)
        trusted.trust_score = min(1.0, trusted.trust_score + 0.005)
        trusted.charge = trusted.trust_score - 0.5
    
    def create_perturbation_event(self, state: HashSphereState, magnitude: float = 1.0) -> Dict:
        """
        Create a significant perturbation event.
        Use sparingly to shake up frozen systems.
        """
        nodes = list(state.nodes.values())
        affected = []
        
        for node in nodes:
            if random.random() < 0.3:  # Affect 30% of nodes
                # Large position perturbation
                node.x += random.gauss(0, 20 * magnitude)
                node.y += random.gauss(0, 20 * magnitude)
                node.z += random.gauss(0, 20 * magnitude)
                
                # Temperature spike
                node.temperature += 0.5 * magnitude
                
                affected.append(node.id)
        
        return {
            "type": "perturbation_event",
            "magnitude": magnitude,
            "affected_nodes": len(affected),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_entropy_metrics(self, state: HashSphereState) -> Dict:
        """
        Compute entropy-related metrics.
        """
        nodes = list(state.nodes.values())
        
        if not nodes:
            return {
                "temperature": 0,
                "trust_variance": 0,
                "value_gini": 0,
                "position_spread": 0,
                "activity_rate": 0
            }
        
        # Temperature
        temps = [n.temperature for n in nodes]
        avg_temp = sum(temps) / len(temps)
        
        # Trust variance (higher = more asymmetry)
        trusts = [n.trust_score for n in nodes]
        avg_trust = sum(trusts) / len(trusts)
        trust_variance = sum((t - avg_trust) ** 2 for t in trusts) / len(trusts)
        
        # Value Gini coefficient (inequality measure)
        values = sorted([n.value for n in nodes])
        n = len(values)
        if sum(values) > 0:
            gini = sum((2 * i - n - 1) * v for i, v in enumerate(values, 1)) / (n * sum(values))
        else:
            gini = 0
        
        # Position spread (how dispersed the system is)
        cx = sum(n.x for n in nodes) / len(nodes)
        cy = sum(n.y for n in nodes) / len(nodes)
        cz = sum(n.z for n in nodes) / len(nodes)
        spread = sum(math.sqrt((n.x-cx)**2 + (n.y-cy)**2 + (n.z-cz)**2) for n in nodes) / len(nodes)
        
        # Activity rate (% of active nodes)
        active = sum(1 for n in nodes if n.status == NodeStatus.ACTIVE)
        activity_rate = active / len(nodes)
        
        return {
            "temperature": avg_temp,
            "trust_variance": trust_variance,
            "value_gini": gini,
            "position_spread": spread,
            "activity_rate": activity_rate,
            "step_count": self.step_count
        }
