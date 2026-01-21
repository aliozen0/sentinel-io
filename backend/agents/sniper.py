import time
import logging
import requests
import json
from typing import List, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# In-Memory Cache (Simple implementation for MVP)
MARKET_CACHE = {
    "timestamp": 0,
    "data": []
}
CACHE_TTL = 300  # 5 minutes

class GPUNode(BaseModel):
    id: str
    gpu_model: str
    price_hourly: float
    reliability: float # 0-100
    speed_score: float # 0-100 (e.g. connection speed / benchmark)
    score: float = 0.0

class Sniper:
    """
    Module 2: THE SNIPER (Market Arbitrage Engine)
    Finds the best price/performance node on io.net.
    """

    @staticmethod
    async def get_best_nodes(gpu_model: str = "RTX 4090", top_k: int = 3, budget_hourly: float = 100.0) -> List[GPUNode]:
        """
        Fetches market data and returns top scored nodes.
        """
        data = Sniper._get_market_data()
        
        # Filter
        candidates = [
            node for node in data 
            if gpu_model.lower() in node['gpu_model'].lower() 
            and node['price_hourly'] <= budget_hourly
        ]
        
        # Parse and Score
        scored_nodes = []
        for c in candidates:
            # Safe parsing
            try:
                price = float(c.get('price_hourly', 9999))
                rel = float(c.get('reliability', 0))
                speed = float(c.get('speed', 0))
                
                # Algorithm: Score = (1 / Price) * 0.6 + (Reliability) * 0.3 + (Speed) * 0.1
                # Normalizing reliability (0-1) and speed (0-1) might be better, but implementing raw formula first.
                # Assuming reliability is 0-100 and speed is relative.
                # To prevent division by zero or super high scores for near-zero price, clamp price.
                safe_price = max(price, 0.01)
                
                # Normalize components to be somewhat comparable? 
                # User prompted: (1/Price) * 0.6. 
                # If Price=0.5 -> 2 * 0.6 = 1.2. If Reliability=100 -> 30. 
                # This suggests Reliability is likely 0-1 or user formula implies different scales.
                # Assuming Reliability 0-1 and Speed 0-1 for balanced scoring, OR Reliability is dominant.
                # Let's stick to the user's prompt blindly for now, but assume Reliability is 0-100 scaling.
                
                score = (1 / safe_price) * 0.6 + (rel / 100.0) * 0.3 + (speed / 100.0) * 0.1
                
                node_obj = GPUNode(
                    id=c['id'],
                    gpu_model=c['gpu_model'],
                    price_hourly=price,
                    reliability=rel,
                    speed_score=speed,
                    score=score
                )
                scored_nodes.append(node_obj)
            except Exception:
                continue

        # Sort by score descending
        scored_nodes.sort(key=lambda x: x.score, reverse=True)
        return scored_nodes[:top_k]

    @staticmethod
    def _get_market_data() -> List[Dict]:
        """
        Circuit Breaker Logic: Cache -> Live -> Snapshot
        """
        current_time = time.time()
        
        # 1. Cache Check
        if current_time - MARKET_CACHE['timestamp'] < CACHE_TTL and MARKET_CACHE['data']:
            logger.info("Serving market data from Cache.")
            return MARKET_CACHE['data']

        # 2. Live Fetch
        try:
            logger.info("Fetching live market data from io.net...")
            # Mocking the official API for MVP as specific endpoint wasn't provided, 
            # or using a placeholder that would fail to trigger fallback for now.
            # In a real scenario: response = requests.get("https://api.io.net/v1/devices...", timeout=5)
            # Raising generic exception to trigger fallback since we don't have a real API key/endpoint for market yet.
            raise requests.exceptions.RequestException("Mocking API failure to use snapshot")
            
            # If success:
            # data = response.json()
            # MARKET_CACHE['timestamp'] = current_time
            # MARKET_CACHE['data'] = data
            # return data

        except Exception as e:
            logger.error(f"Market fetch failed: {e}. Loading Snapshot.")
            # 3. Snapshot Fallback
            return Sniper._load_snapshot()

    @staticmethod
    def _load_snapshot() -> List[Dict]:
        """
        Loads local snapshot for robustness.
        """
        return [
            {"id": "node_1", "gpu_model": "RTX 4090", "price_hourly": 0.45, "reliability": 98, "speed": 85},
            {"id": "node_2", "gpu_model": "RTX 4090", "price_hourly": 0.38, "reliability": 80, "speed": 70},
            {"id": "node_3", "gpu_model": "RTX 3090", "price_hourly": 0.20, "reliability": 95, "speed": 60},
            {"id": "node_4", "gpu_model": "A100", "price_hourly": 1.50, "reliability": 99, "speed": 95},
             {"id": "node_5", "gpu_model": "RTX 4090", "price_hourly": 0.50, "reliability": 99, "speed": 90},
        ]
