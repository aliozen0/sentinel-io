from datetime import datetime
from typing import List, Dict, Optional

class StateManager:
    def __init__(self):
        self.workers: Dict[str, Dict] = {}
        self.worker_history: Dict[str, List[Dict]] = {}
        self.agent_logs: List[Dict] = []
        
        # Tokenomics Ledger
        self.ledger = {
            "balance": 5000.0,
            "slashed": 0.0,
            "rewards": 0.0,
            "history": [] # {"reason": "...", "amount": -10.0, "ts": ...}
        }
        
        # Session Context for Chat
        self.last_analysis = {} # Stores the result of last Auditor/Sniper run
    
    def update_worker_status(self, worker_id: str, data: dict):
        self.workers[worker_id] = {
            "last_seen": datetime.now(),
            "data": data,
            "status": "Active", # Default status
            "status": "Active", # Default status
            "lifecycle_state": "ACTIVE", # IDLE / ACTIVE / CORDONED / DRAINING / OFFLINE
            "integrity": data.get("integrity", "UNKNOWN") # VERIFIED / SPOOFED / UNKNOWN
        }
        
        # Initialize history if not exists
        if worker_id not in self.worker_history:
            self.worker_history[worker_id] = []
            
        # Add to history (keep last 60 entries for ~60 seconds of 1s interval)
        # DeepSim Enterprise needs more data points for trend analysis
        self.worker_history[worker_id].append({
            "timestamp": datetime.now().isoformat(),
            **data # Store FULL telemetry
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

    def transition_node(self, worker_id: str, new_state: str):
        if worker_id in self.workers:
            self.workers[worker_id]["lifecycle_state"] = new_state.upper()
    
    def get_idle_node(self):
        """Returns the first IDLE node found."""
        for wid, info in self.workers.items():
            if info.get("lifecycle_state") == "IDLE":
                return wid
        return None

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

    def update_ledger(self, amount: float, reason: str):
        self.ledger["balance"] += amount
        if amount < 0:
            self.ledger["slashed"] += abs(amount)
        else:
            self.ledger["rewards"] += amount
            
        self.ledger["history"].append({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "amount": amount,
            "reason": reason
        })
        # Keep history short
        if len(self.ledger["history"]) > 20:
             self.ledger["history"].pop(0)

    def get_ledger(self):
        return self.ledger
    
    def add_simulated_worker(self, worker_id: str):
        """Creates a placeholder IDLE worker."""
        self.workers[worker_id] = {
            "last_seen": datetime.now(),
            "data": {
                "temperature": 25.0,
                "latency": 0.05,
                "fan_speed": 0,
                "health": {"cooling": 1.0, "network": 1.0}
            },
            "status": "Active",
            "lifecycle_state": "IDLE", # Starts as Standby
            "integrity": "VERIFIED"
        }

state = StateManager()
