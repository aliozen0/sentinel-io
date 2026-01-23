
import os
import sqlite3
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = "io_guard.db"

class DatabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        
        if self.url and self.key:
            self.mode = "CLOUD"
            try:
                self.supabase: Client = create_client(self.url, self.key)
                logger.info("✅ Database Mode: CLOUD (Supabase)")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Supabase: {e}. Falling back to LOCAL.")
                self.mode = "LOCAL"
        else:
            self.mode = "LOCAL"
            logger.info("⚠️ Database Mode: LOCAL (SQLite) - No Cloud Credentials Found")
        
        if self.mode == "LOCAL":
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database and run migrations if needed."""
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Run Schema
        try:
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r") as f:
                schema_sql = f.read()
                self.conn.executescript(schema_sql)
            logger.info("📂 Local Database Schema Applied.")
            
            # --- Auto-Migration Checks ---
            cursor = self.conn.cursor()
            
            # Check if 'metadata' column exists in 'jobs'
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [info[1] for info in cursor.fetchall()]
            if "metadata" not in columns:
                logger.info("⚠️ Migrating Local DB: Adding 'metadata' column to 'jobs'...")
                cursor.execute("ALTER TABLE jobs ADD COLUMN metadata TEXT")
                self.conn.commit()
            
            # Seed Admin User
            self._seed_local_admin()
            
        except Exception as e:
            logger.error(f"❌ SQLite Init Error: {e}")

    def _seed_local_admin(self):
        try:
            # Import here to avoid circular dependencies if any, or just standard import
            from utils.security import get_password_hash
        except ImportError:
            # Fallback if utils not found (e.g. running script directly)
            logger.warning("Could not import security utils. Admin seed might fail.")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_pw = get_password_hash("1234")
            cursor.execute(
                "INSERT INTO profiles (id, username, credits, password_hash) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), "admin", 1000.00, hashed_pw)
            )
            self.conn.commit()
            logger.info("👤 Local Admin Seeded (User: admin, Pwd: <hashed> 1234)")

    # --- Unified API Methods ---

    def get_user(self, user_id: str) -> Optional[Dict]:
        if self.mode == "CLOUD":
            try:
                # Assuming 'profiles' table exists in Supabase
                res = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase Get User Error: {e}")
            return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def ensure_profile(self, user_id: str, username: str = "unknown") -> bool:
        """Ensures a profile exists for the given user ID."""
        if self.mode == "CLOUD":
            try:
                # Check if exists first to avoid unnecessary upsert if possible, or just upsert
                # Upsert is safer for race conditions
                self.supabase.table("profiles").upsert({
                    "id": user_id,
                    "username": username,
                    # Don't overwrite credits if exists? upsert with ignore_duplicates?
                    # Supabase upsert updates by default. We should check first or use on_conflict
                    # For simplicity, if we are calling this, get_user returned None, so we assume it doesn't exist
                    "credits": 10.0 
                }).execute()
                logger.info(f"Ensured Profile for {user_id} (Cloud)")
                return True
            except Exception as e:
                logger.error(f"Ensure Profile Cloud Error: {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id FROM profiles WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO profiles (id, username, credits) VALUES (?, ?, ?)",
                        (user_id, username, 10.0)
                    )
                    self.conn.commit()
                    logger.info(f"Ensured Profile for {user_id} (Local)")
                return True
            except Exception as e:
                logger.error(f"Ensure Profile Local Error: {e}")
                return False

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Used for Local Login mostly"""
        if self.mode == "CLOUD":
            # For cloud, we normally rely on Supabase Auth, but this helper might exist
            try:
                res = self.supabase.table("profiles").select("*").eq("username", username).execute()
                return res.data[0] if res.data else None
            except: return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def log_chat(self, user_id: str, role: str, content: str):
        if self.mode == "CLOUD":
            try:
                self.supabase.table("chat_messages").insert({
                    "role": role,
                    "content": content,
                    "user_id": user_id
                }).execute()
            except Exception as e:
                logger.error(f"Log Chat Error: {e}")
        else:
            cursor = self.conn.cursor()
            # Assuming 'user_id' can be null or we track it
            cursor.execute(
                "INSERT INTO chat_messages (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            self.conn.commit()

    # --- Credit System Methods ---

    def get_credits(self, user_id: str) -> float:
        """Get current credit balance for user."""
        try:
            user = self.get_user(user_id)
            if user:
                return float(user.get("credits", 0.0))
        except Exception as e:
            logger.error(f"Get Credits Error: {e}")
        return 0.0

    def deduct_credits(self, user_id: str, amount: float, reason: str = "") -> bool:
        """
        Deduct credits from user. Returns True if successful, False if insufficient funds or error.
        This is an atomic operation where possible.
        """
        if amount <= 0:
            return True

        current_credits = self.get_credits(user_id)
        if current_credits < amount:
            logger.warning(f"Insufficient credits for user {user_id}. Needed: {amount}, Has: {current_credits}")
            return False

        new_balance = current_credits - amount

        if self.mode == "CLOUD":
            try:
                # Direct update
                self.supabase.table("profiles").update({"credits": new_balance}).eq("id", user_id).execute()
                logger.info(f"Deducted {amount} credits from {user_id}. New balance: {new_balance}. Reason: {reason}")
                return True
            except Exception as e:
                logger.error(f"Deduct Credits Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE profiles SET credits = ? WHERE id = ?", (new_balance, user_id))
                self.conn.commit()
                logger.info(f"Deducted {amount} credits from {user_id}. New balance: {new_balance} (Local)")
                return True
            except Exception as e:
                logger.error(f"Deduct Credits Error (Local): {e}")
                return False

    def add_credits(self, user_id: str, amount: float, reason: str = "") -> bool:
        """Add credits to user."""
        if amount <= 0:
            return False
            
        current = self.get_credits(user_id)
        new_balance = current + amount
        
        if self.mode == "CLOUD":
            try:
                self.supabase.table("profiles").update({"credits": new_balance}).eq("id", user_id).execute()
                return True
            except Exception as e:
                logger.error(f"Add Credits Error: {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE profiles SET credits = ? WHERE id = ?", (new_balance, user_id))
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Add Credits Error: {e}")
                return False

    # --- Job Management Methods (Persistent Storage) ---

    def create_job(self, job_id: str, mode: str, status: str, metadata: Dict) -> bool:
        """Create a new job record."""
        user_id = metadata.get("user_id") 
        gpu_target = metadata.get("gpu", "")
        
        # Serialize metadata for storage if needed
        import json
        metadata_json = json.dumps(metadata) if self.mode == "LOCAL" else metadata
        
        if self.mode == "CLOUD":
            try:
                self.supabase.table("jobs").insert({
                    "id": job_id,
                    "user_id": user_id,
                    "mode": mode,
                    "status": status,
                    "gpu_target": gpu_target,
                    "metadata": metadata, # Supabase handles JSON/Dict automatically for JSONB
                    "created_at": datetime.now().isoformat()
                }).execute()
                logger.info(f"Created Job {job_id} (Cloud)")
                return True
            except Exception as e:
                logger.error(f"Create Job Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO jobs (id, user_id, mode, status, gpu_target, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (job_id, user_id, mode, status, gpu_target, metadata_json, datetime.now().isoformat())
                )
                self.conn.commit()
                logger.info(f"Created Job {job_id} (Local)")
                return True
            except Exception as e:
                logger.error(f"Create Job Error (Local): {e}")
                return False

    def update_job(self, job_id: str, status: str = None, result: Any = None, **kwargs):
        """Update job status and results."""
        updates = {}
        if status:
            updates["status"] = status
        
        if result:
            # Maybe store in logs_summary or final_cost
            if isinstance(result, dict):
                # If result has logs, save them
                if "logs" in result:
                    updates["logs_summary"] = "\n".join(result["logs"][-100:]) # Limit to last 100 lines
                if "cost" in result:
                    updates["final_cost"] = result["cost"]
                    
        # Support generic metadata update
        if "metadata" in kwargs:
             import json
             meta = kwargs["metadata"]
             if self.mode == "LOCAL" and isinstance(meta, dict):
                 updates["metadata"] = json.dumps(meta)
             else:
                 updates["metadata"] = meta

        if not updates:
            return

        if self.mode == "CLOUD":
            try:
                self.supabase.table("jobs").update(updates).eq("id", job_id).execute()
            except Exception as e:
                logger.error(f"Update Job Error: {e}")
        else:
            try:
                cursor = self.conn.cursor()
                # Dynamic update query
                clauses = [f"{k} = ?" for k in updates.keys()]
                values = list(updates.values()) + [job_id]
                sql = f"UPDATE jobs SET {', '.join(clauses)} WHERE id = ?"
                cursor.execute(sql, values)
                self.conn.commit()
            except Exception as e:
                logger.error(f"Update Job Error: {e}")

    def update_job_status(self, job_id: str, status: str):
        """Wrapper for update_job to match JobManager calls."""
        return self.update_job(job_id, status=status)

    def get_job(self, job_id: str) -> Optional[Dict]:
        if self.mode == "CLOUD":
            try:
                res = self.supabase.table("jobs").select("*").eq("id", job_id).execute()
                return res.data[0] if res.data else None
            except: return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_jobs(self, user_id: str) -> list:
        if self.mode == "CLOUD":
            try:
                res = self.supabase.table("jobs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                return res.data if res.data else []
            except Exception as e:
                logger.error(f"Get User Jobs Error: {e}")
                return []
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

# Helper for Dependency Injection
def get_db():
    return DatabaseClient()
