import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    logger.warning("Supabase URL or Key not found in .env. Database features will be disabled.")
    supabase: Client = None
else:
    try:
        supabase: Client = create_client(url, key)
        logger.info("Connected to Supabase successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        supabase = None

def get_db():
    """Returns the Supabase client instance."""
    return supabase
