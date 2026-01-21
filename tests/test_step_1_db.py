import pytest
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from db.client import get_db

load_dotenv()

def test_supabase_connection():
    """
    Verifies that we can connect to Supabase.
    """
    db = get_db()
    
    if not os.getenv("SUPABASE_KEY"):
        pytest.skip("Skipping DB test: SUPABASE_KEY not found in .env")
        
    assert db is not None, "Failed to initialize Supabase client"

def test_chat_persistence():
    """
    Verifies that we can write and read from 'chat_messages' table.
    """
    db = get_db()
    if not db:
        pytest.skip("DB not available")
        
    # 1. Insert a Test Message
    test_msg = "TEST_AUTOMATION_" + str(os.urandom(4).hex())
    try:
        data = db.table("chat_messages").insert({
            "role": "user",
            "content": test_msg
        }).execute()
        
        # 2. Verify Insert Success
        assert len(data.data) > 0
        inserted_id = data.data[0]['id']
        
        # 3. Read it back
        read_data = db.table("chat_messages").select("*").eq("id", inserted_id).execute()
        assert len(read_data.data) == 1
        assert read_data.data[0]['content'] == test_msg
        
        # 4. Cleanup (Optional, keep for history or delete)
        db.table("chat_messages").delete().eq("id", inserted_id).execute()
        
    except Exception as e:
        pytest.fail(f"Supabase Operation Failed: {e}")

if __name__ == "__main__":
    # Manual run helper
    try:
        test_supabase_connection()
        print("✅ Connection Test Passed")
        test_chat_persistence()
        print("✅ Persistence Test Passed")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
