"""
Hash Sphere Physics Engine

Force-directed simulation where:
- Mass = economic weight
- Charge = trust polarity
- Temperature = activity level
- Gravity = trust attraction
- Repulsion = identity separation
- Entropy = time gradient

This is NOT decoration - it is correct physics for state-space dynamics.
"""

import math
from typing import Dict, List, Tuple
from dataclasses import dataclass
from .models import HashNode, HashEdge, HashSphereState, NodeStatus


@dataclass
class PhysicsConfig:
    """Configuration for the physics simulation"""
    # Force constants
    gravity_constant: float = 0.1       # Attraction between trusted nodes
    repulsion_constant: float = 100.0   # Separation force
    spring_constant: float = 0.05       # Edge spring force
    damping: float = 0.9                # Velocity damping
    
    # Bounds
    max_velocity: float = 10.0
    min_distance: float = 1.0
    max_distance: float = 1000.0
    
    # Time
    dt: float = 0.1                     # Time step
    
    # Temperature effects
    temperature_decay: float = 0.99     # How fast nodes cool
    activity_threshold: float = 0.1     # Below this = cold
    
    # Trust effects
    trust_attraction_multiplier: float = 2.0
    distrust_repulsion_multiplier: float = 1.5


class PhysicsEngine:
    """
    N-body simulation for Hash Sphere.
    
    Forces:
    1. Gravity: Trusted nodes attract each other (forms cores)
    2. Repulsion: All nodes repel (prevents collapse)
    3. Springs: Edges act as springs (maintains structure)
    4. Entropy: Time pushes inactive nodes outward (forms shells)
    """
    
    def __init__(self, config: PhysicsConfig = None):
        self.config = config or PhysicsConfig()
        
    def compute_forces(self, state: HashSphereState) -> Dict[str, Tuple[float, float, float]]:
        """
        Compute net force on each node.
        Returns dict of node_id -> (fx, fy, fz)
        """
        forces = {node_id: [0.0, 0.0, 0.0] for node_id in state.nodes}
        nodes = list(state.nodes.values())
        
        # Pairwise forces (gravity + repulsion)
        for i, node_a in enumerate(nodes):
            for j, node_b in enumerate(nodes[i+1:], i+1):
                fx, fy, fz = self._compute_pairwise_force(node_a, node_b)
                
                forces[node_a.id][0] += fx
                forces[node_a.id][1] += fy
                forces[node_a.id][2] += fz
                
                forces[node_b.id][0] -= fx
                forces[node_b.id][1] -= fy
                forces[node_b.id][2] -= fz
        
        # Spring forces from edges
        for edge in state.edges.values():
            if edge.source in state.nodes and edge.target in state.nodes:
                source = state.nodes[edge.source]
                target = state.nodes[edge.target]
                fx, fy, fz = self._compute_spring_force(source, target, edge)
                
                forces[source.id][0] += fx
                forces[source.id][1] += fy
                forces[source.id][2] += fz
                
                forces[target.id][0] -= fx
                forces[target.id][1] -= fy
                forces[target.id][2] -= fz
        
        # Entropy force (pushes cold nodes outward)
        center = self._compute_center_of_mass(state)
        for node in nodes:
            fx, fy, fz = self._compute_entropy_force(node, center)
            forces[node.id][0] += fx
            forces[node.id][1] += fy
            forces[node.id][2] += fz
        
        return {k: tuple(v) for k, v in forces.items()}
    
    def _compute_pairwise_force(self, a: HashNode, b: HashNode) -> Tuple[float, float, float]:
        """
        Compute force between two nodes.
        
        Combines:
        - Gravitational attraction (based on mass and trust)
        - Electrostatic repulsion (based on charge)
        """
        dx = b.x - a.x
        dy = b.y - a.y
        dz = b.z - a.z
        
        dist_sq = dx*dx + dy*dy + dz*dz
        dist = math.sqrt(dist_sq) if dist_sq > 0 else self.config.min_distance
        dist = max(dist, self.config.min_distance)
        
        # Unit vector
        ux, uy, uz = dx/dist, dy/dist, dz/dist
        
        # Gravitational attraction (trust-weighted)
        trust_factor = (a.trust_score + b.trust_score) / 2
        gravity = self.config.gravity_constant * a.mass * b.mass * trust_factor / dist_sq
        
        # Boost attraction if both nodes trust each other
        if a.charge > 0 and b.charge > 0:
            gravity *= self.config.trust_attraction_multiplier
        
        # Repulsion (always present, prevents collapse)
        repulsion = self.config.repulsion_constant / dist_sq
        
        # Boost repulsion if nodes distrust each other
        if a.charge < 0 or b.charge < 0:
            repulsion *= self.config.distrust_repulsion_multiplier
        
        # Net force (positive = attraction, negative = repulsion)
        net_force = gravity - repulsion
        
        return (net_force * ux, net_force * uy, net_force * uz)
    
    def _compute_spring_force(self, source: HashNode, target: HashNode, edge: HashEdge) -> Tuple[float, float, float]:
        """
        Compute spring force along an edge.
        Edges act as springs with rest length based on edge weight.
        """
        dx = target.x - source.x
        dy = target.y - source.y
        dz = target.z - source.z
        
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        dist = max(dist, self.config.min_distance)
        
        # Rest length inversely proportional to edge weight
        rest_length = 50.0 / (edge.weight + 0.1)
        
        # Spring force (Hooke's law)
        displacement = dist - rest_length
        force = self.config.spring_constant * displacement * edge.weight
        
        # Unit vector
        ux, uy, uz = dx/dist, dy/dist, dz/dist
        
        return (force * ux, force * uy, force * uz)
    
    def _compute_entropy_force(self, node: HashNode, center: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """
        Compute entropy force.
        Cold/inactive nodes are pushed outward (forms shells).
        Hot/active nodes are pulled inward (forms cores).
        """
        dx = node.x - center[0]
        dy = node.y - center[1]
        dz = node.z - center[2]
        
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        dist = max(dist, self.config.min_distance)
        
        # Unit vector (outward from center)
        ux, uy, uz = dx/dist, dy/dist, dz/dist
        
        # Entropy force: cold nodes pushed out, hot nodes pulled in
        # Temperature < 1 = outward, Temperature > 1 = inward
        entropy_force = (1.0 - node.temperature) * 0.5
        
        # Cold nodes (low activity) drift outward
        if node.status in [NodeStatus.COLD, NodeStatus.COOLING, NodeStatus.DECAYING]:
            entropy_force = abs(entropy_force) * 2.0
        
        return (entropy_force * ux, entropy_force * uy, entropy_force * uz)
    
    def _compute_center_of_mass(self, state: HashSphereState) -> Tuple[float, float, float]:
        """Compute mass-weighted center of the system"""
        if not state.nodes:
            return (0.0, 0.0, 0.0)
        
        total_mass = sum(n.mass for n in state.nodes.values())
        if total_mass == 0:
            total_mass = 1.0
        
        cx = sum(n.x * n.mass for n in state.nodes.values()) / total_mass
        cy = sum(n.y * n.mass for n in state.nodes.values()) / total_mass
        cz = sum(n.z * n.mass for n in state.nodes.values()) / total_mass
        
        return (cx, cy, cz)
    
    def step(self, state: HashSphereState) -> HashSphereState:
        """
        Advance simulation by one time step.
        Updates positions and velocities of all nodes.
        """
        forces = self.compute_forces(state)
        
        for node_id, (fx, fy, fz) in forces.items():
            node = state.nodes[node_id]
            
            # F = ma, so a = F/m
            ax = fx / max(node.mass, 0.1)
            ay = fy / max(node.mass, 0.1)
            az = fz / max(node.mass, 0.1)
            
            # Update velocity
            node.vx = (node.vx + ax * self.config.dt) * self.config.damping
            node.vy = (node.vy + ay * self.config.dt) * self.config.damping
            node.vz = (node.vz + az * self.config.dt) * self.config.damping
            
            # Clamp velocity
            speed = math.sqrt(node.vx**2 + node.vy**2 + node.vz**2)
            if speed > self.config.max_velocity:
                scale = self.config.max_velocity / speed
                node.vx *= scale
                node.vy *= scale
                node.vz *= scale
            
            # Update position
            node.x += node.vx * self.config.dt
            node.y += node.vy * self.config.dt
            node.z += node.vz * self.config.dt
            
            # Decay temperature
            node.temperature *= self.config.temperature_decay
            
            # Update status based on temperature
            if node.temperature < self.config.activity_threshold:
                if node.status == NodeStatus.ACTIVE:
                    node.status = NodeStatus.COOLING
                elif node.status == NodeStatus.COOLING:
                    node.status = NodeStatus.COLD
        
        # Update global metrics
        state.entropy = state.compute_entropy()
        state.temperature = sum(n.temperature for n in state.nodes.values()) / max(len(state.nodes), 1)
        
        return state
    
    def run_simulation(self, state: HashSphereState, steps: int = 100) -> HashSphereState:
        """Run simulation for multiple steps"""
        for _ in range(steps):
            state = self.step(state)
        return state
    
    def detect_instability(self, state: HashSphereState) -> List[Dict]:
        """
        Detect instabilities in the system.
        Returns list of instability events.
        """
        instabilities = []
        
        # Check for collapsed nodes
        for node in state.nodes.values():
            if node.status == NodeStatus.COLLAPSED:
                instabilities.append({
                    "type": "collapse",
                    "node_id": node.id,
                    "severity": "critical",
                    "message": f"Node {node.id} has collapsed"
                })
        
        # Check for runaway velocities
        for node in state.nodes.values():
            speed = math.sqrt(node.vx**2 + node.vy**2 + node.vz**2)
            if speed > self.config.max_velocity * 0.9:
                instabilities.append({
                    "type": "runaway",
                    "node_id": node.id,
                    "severity": "high",
                    "message": f"Node {node.id} approaching escape velocity"
                })
        
        # Check for extreme clustering
        center = self._compute_center_of_mass(state)
        distances = []
        for node in state.nodes.values():
            d = math.sqrt((node.x - center[0])**2 + (node.y - center[1])**2 + (node.z - center[2])**2)
            distances.append(d)
        
        if distances:
            avg_dist = sum(distances) / len(distances)
            if avg_dist < 10.0:
                instabilities.append({
                    "type": "collapse_risk",
                    "severity": "high",
                    "message": "System approaching gravitational collapse"
                })
            elif avg_dist > 500.0:
                instabilities.append({
                    "type": "dispersion_risk",
                    "severity": "medium",
                    "message": "System dispersing - losing coherence"
                })
        
        return instabilities
