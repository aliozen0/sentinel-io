import pytest
import asyncio
import sys
import os

# Add backend to path
# Add project root to path (assuming script is in /app/tests and root is /app)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sniper import Sniper, MARKET_CACHE

@pytest.mark.asyncio
async def test_sniper_market_scraping():
    """
    Verifies that Sniper can scrape io.net (or fallback gracefully).
    """
    print("\nStarting Sniper Market Test...")
    
    # 1. Clear Cache to force fresh fetch
    MARKET_CACHE['data'] = []
    MARKET_CACHE['timestamp'] = 0
    
    # 2. Trigger Scrape
    try:
        nodes = await Sniper.get_best_nodes(gpu_model="RTX 4090", top_k=5)
        
        # 3. Validation
        assert len(nodes) > 0, "No nodes returned!"
        print(f"✅ Successfully found {len(nodes)} nodes.")
        
        first_node = nodes[0]
        print(f"🏆 Top Candidate: {first_node.gpu_model} - ${first_node.price_hourly}/hr (Score: {first_node.score:.2f})")
        print(f"   📊 Stats: {first_node.idle_nodes}/{first_node.total_nodes} Idle (Availability), {first_node.hired_nodes} Hired (Popularity)")
        
        # Check if it looks like real data (optional)
        if first_node.id.startswith("node_"):
            print("⚠️ Note: Returned nodes look like Snapshot data (Scraping might have failed or triggered Circuit Breaker).")
        else:
            print("🎉 Confirmed: Data appears to be from Live Scraping!")
            
    except Exception as e:
        pytest.fail(f"Sniper crashed: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_sniper_market_scraping())
