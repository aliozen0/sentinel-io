
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from db.client import get_db
from utils.security import verify_password
from auth import create_local_token, get_current_user

router = APIRouter()

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Returns current user profile.
    """
    return current_user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    [Local Mode] Authenticates user against SQLite DB using Bcrypt hash.
    """
    db = get_db()
    db = get_db()
    # Hybrid Auth: Allow generic login even in Cloud Mode
    # if db.mode == "CLOUD": ... (removed constraints)
    
    # Fetch User
    user = db.get_user_by_username(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials user not found")
        
    # Verify Password
    hashed_pw = user.get("password_hash")
    if not hashed_pw:
        # User might exist but no password set (e.g. legacy or cloud synced profile without hash)
        raise HTTPException(status_code=401, detail="Invalid credentials (no password set)")

    if not verify_password(form_data.password, hashed_pw):
         raise HTTPException(status_code=401, detail="Invalid credentials")
         
    # Generate Token
    token = create_local_token(user['id'], user['username'])
    return {"access_token": token, "token_type": "bearer"}
