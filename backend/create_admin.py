
import os
import uuid
import asyncio
from dotenv import load_dotenv
from supabase import create_client

# Local Security Utils (Ensure backend is in PYTHONPATH)
try:
    from utils.security import get_password_hash
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.security import get_password_hash

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not set in .env")
    exit(1)

supabase = create_client(URL, KEY)

def seed_admin():
    print(f"🔌 Connecting to Supabase: {URL}")
    
    username = "admin"
    password = "1234"
    hashed_pw = get_password_hash(password)
    user_id = str(uuid.uuid4())
    
    # Check if exists
    try:
        res = supabase.table("profiles").select("*").eq("username", username).execute()
        if res.data:
            print(f"⚠️ User '{username}' already exists. Skipping.")
            return
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return

    # Insert
    try:
        data = {
            "id": user_id,
            "username": username,
            "credits": 1000.00,
            "password_hash": hashed_pw
        }
        supabase.table("profiles").insert(data).execute()
        print(f"✅ Success! User '{username}' created with password '{password}'")
        print("🚀 You can now login via the Frontend.")
    except Exception as e:
        print(f"❌ Failed to create user: {e}")

if __name__ == "__main__":
    seed_admin()
