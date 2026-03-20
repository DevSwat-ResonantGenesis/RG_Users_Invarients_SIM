"""
State Physics Service - Production Readiness Tests

Tests to verify the service is production-ready:
1. API endpoints respond correctly
2. Demo generation works
3. Simulation runs without errors
4. Conservation laws are preserved
5. Performance is acceptable
"""

import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8091"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Health endpoint should return ok"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "hash-sphere-visualizer"
    
    @pytest.mark.asyncio
    async def test_root_serves_frontend(self):
        """Root should serve the frontend HTML"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_api_state_endpoint(self):
        """State endpoint should return valid structure"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/state")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)


class TestDemoGeneration:
    """Tests for demo data generation"""
    
    @pytest.mark.asyncio
    async def test_generate_small_demo(self):
        """Small demo should generate quickly"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            start = time.time()
            response = await client.post(f"{BASE_URL}/api/demo?num_users=20&num_transactions=50")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert len(data["nodes"]) >= 20
            assert elapsed < 5.0, f"Demo generation took too long: {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_generate_galaxy(self):
        """Galaxy generation should work within time limit"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = time.time()
            response = await client.post(
                f"{BASE_URL}/api/galaxy",
                json={
                    "num_users": 100,
                    "num_transactions": 300,
                    "num_services": 5,
                    "enable_agent": False,
                    "enable_entropy": False
                }
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["nodes"] >= 100
            assert elapsed < 30.0, f"Galaxy generation took too long: {elapsed}s"


class TestSimulation:
    """Tests for physics simulation"""
    
    @pytest.mark.asyncio
    async def test_simulation_step(self):
        """Single simulation step should work"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First generate some data
            await client.post(f"{BASE_URL}/api/demo?num_users=10&num_transactions=20")
            
            # Run simulation step
            response = await client.post(f"{BASE_URL}/api/simulate/step")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
    
    @pytest.mark.asyncio
    async def test_simulation_multiple_steps(self):
        """Multiple simulation steps should complete"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate data
            await client.post(f"{BASE_URL}/api/demo?num_users=20&num_transactions=50")
            
            # Run 50 steps
            start = time.time()
            response = await client.post(
                f"{BASE_URL}/api/simulate",
                json={"steps": 50}
            )
            elapsed = time.time() - start
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert elapsed < 10.0, f"Simulation took too long: {elapsed}s"


class TestConservationLaws:
    """Tests for invariant preservation"""
    
    @pytest.mark.asyncio
    async def test_invariants_check(self):
        """Invariants endpoint should work"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/invariants")
            assert response.status_code == 200
            data = response.json()
            assert "invariants" in data
            assert "violations" in data
    
    @pytest.mark.asyncio
    async def test_no_violations_after_demo(self):
        """Demo generation should not create violations"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate demo
            await client.post(f"{BASE_URL}/api/demo?num_users=20&num_transactions=50")
            
            # Check invariants
            response = await client.get(f"{BASE_URL}/api/invariants")
            data = response.json()
            
            # Should have no violations
            assert len(data["violations"]) == 0, f"Violations found: {data['violations']}"
    
    @pytest.mark.asyncio
    async def test_no_violations_after_simulation(self):
        """Simulation should preserve invariants"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate and simulate
            await client.post(f"{BASE_URL}/api/demo?num_users=20&num_transactions=50")
            await client.post(f"{BASE_URL}/api/simulate", json={"steps": 100})
            
            # Check invariants
            response = await client.get(f"{BASE_URL}/api/invariants")
            data = response.json()
            
            assert len(data["violations"]) == 0, f"Violations after simulation: {data['violations']}"


class TestMetrics:
    """Tests for metrics and monitoring"""
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Metrics endpoint should return data"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "node_count" in data or "nodes" in data or isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_entropy_metrics(self):
        """Entropy metrics should be available"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/entropy")
            assert response.status_code == 200


class TestAgentSystem:
    """Tests for agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_spawn(self):
        """Agent spawning should work"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First generate universe
            await client.post(f"{BASE_URL}/api/demo?num_users=10&num_transactions=20")
            
            # Spawn agent
            response = await client.post(f"{BASE_URL}/api/agent/spawn?budget=1000")
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") == True or "agent" in data
    
    @pytest.mark.asyncio
    async def test_agent_status(self):
        """Agent status should be retrievable"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/agent")
            assert response.status_code == 200


class TestReset:
    """Tests for reset functionality"""
    
    @pytest.mark.asyncio
    async def test_reset_universe(self):
        """Reset should clear all data"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Generate data
            await client.post(f"{BASE_URL}/api/demo?num_users=20&num_transactions=50")
            
            # Reset
            response = await client.post(f"{BASE_URL}/api/reset")
            assert response.status_code == 200
            
            # Verify empty
            state_response = await client.get(f"{BASE_URL}/api/state")
            data = state_response.json()
            assert len(data["nodes"]) == 0


class TestPerformance:
    """Performance benchmarks"""
    
    @pytest.mark.asyncio
    async def test_response_time_health(self):
        """Health check should be fast"""
        async with httpx.AsyncClient() as client:
            start = time.time()
            await client.get(f"{BASE_URL}/health")
            elapsed = time.time() - start
            assert elapsed < 0.5, f"Health check too slow: {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_response_time_state(self):
        """State retrieval should be fast"""
        async with httpx.AsyncClient() as client:
            start = time.time()
            await client.get(f"{BASE_URL}/api/state")
            elapsed = time.time() - start
            assert elapsed < 1.0, f"State retrieval too slow: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
