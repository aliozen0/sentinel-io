import os
from dotenv import load_dotenv

# Try loading from file (if exists)
load_dotenv()

url = os.environ.get("SUPABASE_URL", "NOT_SET")
key = os.environ.get("SUPABASE_KEY", "NOT_SET")

print(f"--- DEBUG ENVIRONMENT ---")
print(f"SUPABASE_URL: {url}")
# Mask Key for security but show prefix/length
masked_key = key[:5] + "..." + key[-5:] if len(key) > 10 else key
print(f"SUPABASE_KEY: {masked_key}")
print(f"Starts with 'ey'? {'Yes' if key.startswith('ey') else 'No'}")
print(f"Starts with 'sb'? {'Yes' if key.startswith('sb') else 'No'}")
