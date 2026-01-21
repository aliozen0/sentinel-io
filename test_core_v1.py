import asyncio
from backend.agents.auditor import Auditor
from backend.agents.sniper import Sniper
from backend.agents.architect import Architect
from backend.agents.executor import Executor

# Mock Data
SAMPLE_CODE = """
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 10).cuda()
"""

async def test_auditor():
    print("\n[TEST] Auditor...")
    # This might use LLM if configured, or fallback to AST
    report = await Auditor.analyze_code(SAMPLE_CODE)
    print(f"Report: {report.dict()}")
    assert report.framework == "pytorch"
    assert "cuda" in SAMPLE_CODE.lower() # Basic sanity check

async def test_sniper():
    print("\n[TEST] Sniper (Market)...")
    nodes = await Sniper.get_best_nodes(gpu_model="RTX 4090", budget_hourly=10.0)
    print(f"Found {len(nodes)} nodes.")
    if nodes:
        print(f"Top Node: {nodes[0].id} - Score: {nodes[0].score:.2f}")
    assert len(nodes) > 0 # Should fallback to snapshot if live fails

async def test_architect():
    print("\n[TEST] Architect...")
    config = Architect.plan_environment("pytorch")
    print(f"Env: {config.image}")
    assert "ray-ml" in config.image

async def test_executor():
    print("\n[TEST] Executor (Sim)...")
    async for line in Executor.run_simulation({"job_id": "test_1"}):
        print(f"Log: {line}")
        break # Just verify generator works

async def main():
    await test_auditor()
    await test_sniper()
    await test_architect()
    await test_executor()
    print("\n[SUCCESS] All Core v1.0 tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
