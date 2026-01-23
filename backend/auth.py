
import os
import logging
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.client import get_db, DatabaseClient

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Default secret for Local Mode
LOCAL_SECRET_KEY = "local-dev-secret-key-change-in-prod"
ALGORITHM = "HS256"

def get_jwt_secret():
    """Returns the JWT secret based on mode."""
    db = get_db()
    if db.mode == "CLOUD":
        # Supabase JWT Secret should be in env
        secret = os.environ.get("SUPABASE_JWT_SECRET")
        if not secret:
            logger.warning("CLOUD mode but SUPABASE_JWT_SECRET not found. Auth may fail.")
            return LOCAL_SECRET_KEY # Fallback (risky in prod, ok for hackathon)
        return secret
    return LOCAL_SECRET_KEY

def create_local_token(user_id: str, username: str = "admin") -> str:
    """Generates a local JWT token (valid 24h)."""
    payload = {
        "sub": user_id,
        "username": username,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=24),
        "aud": "authenticated" # Matches Supabase standard
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verifies JWT from Bearer header.
    Works for both Supabase tokens and Local tokens.
    """
    token = credentials.credentials
    secret = get_jwt_secret()
    
    try:
        # 1. Decode Token
        # Supabase tokens might need 'aud' check, we can be lenient or specific
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"verify_aud": False})
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no sub")
            
        # 2. Check Expiration
        # jwt.decode handles 'exp' verification by default
        
        # 3. Fetch User Context from DB
        db = get_db()
        user = db.get_user(user_id)
        
        if not user:
            # If user exists in Token but not DB? (Rare, maybe sync issue or switching modes)
            logger.warning(f"User {user_id} authenticated but not found in DB. Auto-provisioning...")
            
            # Extract info from payload
            username = payload.get("username") or payload.get("email", "user").split("@")[0]
            
            # JIT Provisioning
            db.ensure_profile(user_id, username)
            
            # Fetch again or return basic structure
            user = db.get_user(user_id)
            if not user:
                 # If still fails, return ephemeral (will likely fail FK later but we tried)
                 return {
                    "id": user_id,
                    "username": username,
                    "credits": 0.0,
                    "mode": db.mode
                 }
            
        return {**user, "mode": db.mode}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
