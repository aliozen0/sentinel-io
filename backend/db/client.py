
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
                self.supabase.table("io_chat_history").insert({
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

    # --- Job Management Methods (Persistent Storage) ---

    def create_job(self, job_id: str, job_type: str, status: str, metadata: Dict) -> bool:
        """
        Creates a new job record. Stores only safe metadata (no credentials).
        """
        # Filter out sensitive data before storing
        safe_metadata = {k: v for k, v in metadata.items() 
                         if k not in ('private_key', 'password', 'passphrase')}
        
        if self.mode == "CLOUD":
            try:
                self.supabase.table("jobs").insert({
                    "id": job_id,
                    "status": status,
                    "mode": job_type,
                    "logs_summary": str(safe_metadata)
                }).execute()
                return True
            except Exception as e:
                logger.error(f"Create Job Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO jobs (id, status, mode, logs_summary) VALUES (?, ?, ?, ?)",
                    (job_id, status, job_type, str(safe_metadata))
                )
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Create Job Error (Local): {e}")
                return False

    def update_job_status(self, job_id: str, status: str, logs_summary: str = None) -> bool:
        """Updates job status and optionally appends to logs."""
        if self.mode == "CLOUD":
            try:
                update_data = {"status": status}
                if logs_summary:
                    update_data["logs_summary"] = logs_summary
                self.supabase.table("jobs").update(update_data).eq("id", job_id).execute()
                return True
            except Exception as e:
                logger.error(f"Update Job Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                if logs_summary:
                    cursor.execute(
                        "UPDATE jobs SET status = ?, logs_summary = ? WHERE id = ?",
                        (status, logs_summary, job_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE jobs SET status = ? WHERE id = ?",
                        (status, job_id)
                    )
                self.conn.commit()
                return True
            except Exception as e:
                logger.error(f"Update Job Error (Local): {e}")
                return False

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Retrieves a job by ID."""
        if self.mode == "CLOUD":
            try:
                res = self.supabase.table("jobs").select("*").eq("id", job_id).execute()
                return res.data[0] if res.data else None
            except Exception as e:
                logger.error(f"Get Job Error (Cloud): {e}")
                return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Credit Management Methods ---

    def get_credits(self, user_id: str) -> float:
        """Get user's current credit balance."""
        if self.mode == "CLOUD":
            try:
                res = self.supabase.table("profiles").select("credits").eq("id", user_id).execute()
                if res.data:
                    return float(res.data[0].get("credits", 0.0))
            except Exception as e:
                logger.error(f"Get Credits Error (Cloud): {e}")
            return 0.0
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT credits FROM profiles WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return float(row["credits"]) if row else 0.0

    def deduct_credits(self, user_id: str, amount: float, reason: str = "") -> bool:
        """
        Deducts credits from user account.
        Returns False if insufficient credits.
        """
        current_credits = self.get_credits(user_id)
        
        if current_credits < amount:
            logger.warning(f"Insufficient credits: {user_id} has {current_credits}, needs {amount}")
            return False
        
        new_balance = current_credits - amount
        
        if self.mode == "CLOUD":
            try:
                self.supabase.table("profiles").update({
                    "credits": new_balance
                }).eq("id", user_id).execute()
                logger.info(f"💳 Credit deducted: {user_id} -{amount} ({reason}). New balance: {new_balance}")
                return True
            except Exception as e:
                logger.error(f"Deduct Credits Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE profiles SET credits = ? WHERE id = ?",
                    (new_balance, user_id)
                )
                self.conn.commit()
                logger.info(f"💳 Credit deducted: {user_id} -{amount} ({reason}). New balance: {new_balance}")
                return True
            except Exception as e:
                logger.error(f"Deduct Credits Error (Local): {e}")
                return False

    def add_credits(self, user_id: str, amount: float, reason: str = "") -> bool:
        """Adds credits to user account."""
        current_credits = self.get_credits(user_id)
        new_balance = current_credits + amount
        
        if self.mode == "CLOUD":
            try:
                self.supabase.table("profiles").update({
                    "credits": new_balance
                }).eq("id", user_id).execute()
                logger.info(f"💰 Credit added: {user_id} +{amount} ({reason}). New balance: {new_balance}")
                return True
            except Exception as e:
                logger.error(f"Add Credits Error (Cloud): {e}")
                return False
        else:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE profiles SET credits = ? WHERE id = ?",
                    (new_balance, user_id)
                )
                self.conn.commit()
                logger.info(f"💰 Credit added: {user_id} +{amount} ({reason}). New balance: {new_balance}")
                return True
            except Exception as e:
                logger.error(f"Add Credits Error (Local): {e}")
                return False

# Helper for Dependency Injection
def get_db():
    return DatabaseClient()


