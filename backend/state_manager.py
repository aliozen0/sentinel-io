from datetime import datetime
from typing import List, Dict, Optional

class StateManager:
    def __init__(self):
        self.workers: Dict[str, Dict] = {}
        self.worker_history: Dict[str, List[Dict]] = {}
        self.agent_logs: List[Dict] = []
    
    def update_worker_status(self, worker_id: str, data: dict):
        self.workers[worker_id] = {
            "last_seen": datetime.now(),
            "data": data,
            "status": "Active" # Default status
        }
        
        # Initialize history if not exists
        if worker_id not in self.worker_history:
            self.worker_history[worker_id] = []
            
        # Add to history (keep last 60 entries for ~60 seconds of 1s interval)
        # DeepSim Enterprise needs more data points for trend analysis
        self.worker_history[worker_id].append({
            "timestamp": datetime.now().isoformat(),
            **data # Store FULL telemetry (temp, fan, load, etc.)
        })
        if len(self.worker_history[worker_id]) > 60:
            self.worker_history[worker_id].pop(0)

    def add_agent_log(self, log_entry: dict):
        """
        Global bus for agent events.
        """
        # Ensure timestamp
        if "timestamp" not in log_entry:
            log_entry["timestamp"] = datetime.now().strftime("%H:%M:%S")
            
        self.agent_logs.append(log_entry)
        # Keep last 100 events
        if len(self.agent_logs) > 100:
            self.agent_logs.pop(0)
            
    def get_agent_logs(self, limit: int = 50):
        return self.agent_logs[-limit:]

    def get_all_workers(self):
        # Update statuses based on last_seen (e.g. timeout > 5s = Offline)
        now = datetime.now()
        for worker_id, info in self.workers.items():
            if (now - info["last_seen"]).total_seconds() > 30:
                info["status"] = "Offline"
        return self.workers

    def get_worker_history(self, worker_id: str):
        return self.worker_history.get(worker_id, [])

    def kill_worker(self, worker_id: str):
        if worker_id in self.workers:
            self.workers[worker_id]["status"] = "Killed"

state = StateManager()
