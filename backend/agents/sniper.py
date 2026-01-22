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
    speed_score: float # 0-100
    # New Metrics
    total_nodes: int = 0
    idle_nodes: int = 0
    hired_nodes: int = 0
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
            try:
                price = float(c.get('price_hourly', 9999))
                # New fields
                total = int(c.get('total_nodes', 1))
                idle = int(c.get('idle_nodes', 0))
                hired = int(c.get('hired_nodes', 0))
                
                safe_price = max(price, 0.01)
                
                # --- SMART SNIPER v2 SCORING ALGORITHM ---
                
                # 1. Price Score (Lower is better) - Weight: 40%
                score_price = (1 / safe_price)
                
                # 2. Reliability Score (High uptime critical) - Weight: 30%
                # Normalize 0-100 to 0-1
                reliability = float(c.get('reliability', 95))
                score_reliability = (reliability / 100.0) * 2  # Boost factor
                
                # 3. Availability/Speed Score - Weight: 20%
                speed = float(c.get('speed', 80))
                availability_ratio = (idle / max(total, 1))
                score_performance = (availability_ratio + (speed / 100.0)) / 2
                
                # 4. Trust Score (Logarithmic popularity) - Weight: 10%
                import math
                score_trust = math.log10(max(hired, 1)) 
                
                # Final Weighted Score
                # Price(40%) + Reliability(30%) + Performance(20%) + Trust(10%)
                final_score = (score_price * 0.4) + \
                              (score_reliability * 0.3 * 10) + \
                              (score_performance * 0.2 * 10) + \
                              (score_trust * 0.1)
                
                node_obj = GPUNode(
                    id=c['id'],
                    gpu_model=c['gpu_model'],
                    price_hourly=price,
                    reliability=reliability,
                    speed_score=speed,
                    total_nodes=total,
                    idle_nodes=idle,
                    hired_nodes=hired,
                    score=final_score
                )
                scored_nodes.append(node_obj)
            except Exception as e:
                # logger.warning(f"Skipping node calc: {e}")
                continue

        # Sort by score descending
        scored_nodes.sort(key=lambda x: x.score, reverse=True)
        return scored_nodes[:top_k]

    @staticmethod
    def _scrape_market_data() -> List[Dict]:
        """
        Fetches data from discovered internal API (market-snapshot).
        """
        from fake_useragent import UserAgent

        url = "https://api.io.solutions/v1/io-explorer/network/market-snapshot"
        ua = UserAgent()
        
        headers = {
            "User-Agent": ua.random,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://explorer.io.net/",
            "Origin": "https://explorer.io.net"
        }

        try:
            logger.info(f"Fetching Market API: {url}...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            nodes = []

            # Structure: {"data": [{"hardware_name": "...", "price": 0.25}, ...]}
            raw_items = data.get("data", [])
            
            if not raw_items:
                 logger.warning(f"API returned empty list.")
                 raise ValueError("Empty API response")

            for i, item in enumerate(raw_items):
                try:
                    # Precise extraction based on verified JSON
                    model = item.get("hardware_name", "Unknown GPU")
                    price = item.get("price", 999.0)
                    
                    # Ensure numeric
                    if isinstance(price, str):
                         price = float(price.replace("$", "").replace("/hr", ""))
                    
                    nodes.append({
                        "id": str(item.get("id", f"api_node_{i}")), 
                        "gpu_model": str(model), 
                        "price_hourly": float(price),
                        "reliability": float(item.get("reliability", 98.0)), # Default if missing
                        "speed": float(item.get("speed", 90.0)),
                        # New Metrics
                        "total_nodes": int(item.get("total", 0)),
                        "idle_nodes": int(item.get("idle", 0)),
                        "hired_nodes": int(item.get("hired", 0))
                    })
                except Exception:
                    continue

            # Update Cache
            MARKET_CACHE['timestamp'] = time.time()
            MARKET_CACHE['data'] = nodes
            
            # --- PERSISTENCE LAYER ---
            # 1. Save to File (Local Fallback)
            try:
                import os
                save_path = "market_snapshot.json" 
                with open(save_path, "w") as f:
                    json.dump([n for n in nodes], f, indent=2)
                logger.info(f"Market data saved to {save_path}")
            except Exception as e:
                logger.error(f"Failed to save market snapshot to file: {e}")

            # 2. Save to DB (Supabase)
            try:
                from db.client import get_db
                db = get_db()
                if db:
                    # JSONB format requires list of dicts
                    db.table("market_snapshots").insert({
                        "raw_data": nodes
                    }).execute()
                    logger.info("Market data saved to Supabase.")
            except Exception as e:
                logger.error(f"Failed to save market snapshot to DB: {e}")

            return nodes

        except Exception as e:
            logger.error(f"API Fetch failed: {e}")
            raise e 

    @staticmethod
    def _get_market_data() -> List[Dict]:
        """
        Circuit Breaker Logic: Cache -> Live Scraping -> Snapshot
        """
        curr = time.time()
        if curr - MARKET_CACHE['timestamp'] < CACHE_TTL and MARKET_CACHE['data']:
            return MARKET_CACHE['data']

        try:
            return Sniper._scrape_market_data()
        except Exception:
            # Fallback to Snapshot
            return Sniper._load_snapshot()

    @staticmethod
    def _load_snapshot() -> List[Dict]:
        """
        Loads local snapshot for robustness.
        Priority:
        1. 'market_snapshot.json' (Last successful scrape)
        2. Hardcoded Fallback (If file missing/corrupt)
        """
        try:
            import os
            if os.path.exists("market_snapshot.json"):
                with open("market_snapshot.json", "r") as f:
                    data = json.load(f)
                    if data:
                        logger.info("Loaded market data from 'market_snapshot.json'.")
                        return data
        except Exception as e:
            logger.warning(f"Failed to load local snapshot file: {e}")

        logger.warning("Using Hardcoded Snapshot Fallback.")
        return [
            {"id": "node_1", "gpu_model": "RTX 4090", "price_hourly": 0.45, "reliability": 98, "speed": 85},
            {"id": "node_2", "gpu_model": "RTX 4090", "price_hourly": 0.38, "reliability": 80, "speed": 70},
            {"id": "node_3", "gpu_model": "RTX 3090", "price_hourly": 0.20, "reliability": 95, "speed": 60},
            {"id": "node_4", "gpu_model": "A100", "price_hourly": 1.50, "reliability": 99, "speed": 95},
             {"id": "node_5", "gpu_model": "RTX 4090", "price_hourly": 0.50, "reliability": 99, "speed": 90},
        ]
