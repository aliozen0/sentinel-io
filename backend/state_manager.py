from datetime import datetime
from typing import List, Dict, Optional

class StateManager:
    def __init__(self):
        self.workers: Dict[str, Dict] = {}
        self.worker_history: Dict[str, List[Dict]] = {}
    
    def update_worker_status(self, worker_id: str, data: dict):
        self.workers[worker_id] = {
            "last_seen": datetime.now(),
            "data": data,
            "status": "Active" # Default status
        }
        
        # Initialize history if not exists
        if worker_id not in self.worker_history:
            self.worker_history[worker_id] = []
            
        # Add to history (keep last 30 entries for ~30 seconds of 1s interval)
        self.worker_history[worker_id].append({
            "timestamp": datetime.now(),
            "latency": data.get("latency", 0)
        })
        if len(self.worker_history[worker_id]) > 30:
            self.worker_history[worker_id].pop(0)

    def get_all_workers(self):
        # Update statuses based on last_seen (e.g. timeout > 5s = Offline)
        now = datetime.now()
        for worker_id, info in self.workers.items():
            if (now - info["last_seen"]).total_seconds() > 5:
                info["status"] = "Offline"
        return self.workers

    def get_worker_history(self, worker_id: str):
        return self.worker_history.get(worker_id, [])

    def kill_worker(self, worker_id: str):
        if worker_id in self.workers:
            self.workers[worker_id]["status"] = "Killed"

state = StateManager()
