from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from app.db.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services import schwab_service
from app.api.schwab_api.client import Client
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

security = HTTPBearer()

router = APIRouter()

class SchwabInitialCredentials(BaseModel):
    api_key: str
    api_secret: str

class SchwabOAuthCode(BaseModel):
    code: str

@router.post("/schwab/init-link")
async def init_schwab_link(
    credentials: SchwabInitialCredentials,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    token: str = Depends(security)
):
    # Save initial credentials
    await db.execute("""
        INSERT INTO api_keys (user_id, key_name, api_key, api_secret, last_used)
        VALUES (:user_id, 'schwab', :api_key, :api_secret, :last_used)
        ON CONFLICT (user_id, key_name) DO UPDATE
        SET api_key = :api_key, api_secret = :api_secret, last_used = :last_used
    """, {
        "user_id": current_user.user_id,
        "api_key": credentials.api_key,
        "api_secret": credentials.api_secret,
        "last_used": datetime.utcnow().isoformat()
    })

    # Initialize Schwab client
    client = Client(current_user.user_id, credentials.api_key, credentials.api_secret, "https://127.0.0.1")
    
    # Get the authorization URL
    auth_url = client.tokens.get_refresh_token_auth_url()

    return {"auth_url": auth_url}

@router.post("/schwab/complete-link")
async def complete_schwab_link(
    oauth_code: SchwabOAuthCode,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    # Retrieve the saved credentials
    credentials = await db.fetch_one(
        "SELECT * FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
        {"user_id": current_user.id}
    )

    if not credentials:
        raise HTTPException(status_code=400, detail="Schwab linking process not initiated")

    # Initialize Schwab client
    client = Client(current_user.id, credentials['api_key'], credentials['api_secret'], "https://127.0.0.1")

    # Exchange the code for tokens
    try:
        await client.tokens.update_refresh_token_from_code(oauth_code.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for tokens: {str(e)}")

    # Update the database with the new tokens
    await db.execute("""
        UPDATE api_keys
        SET access_token = :access_token, refresh_token = :refresh_token, last_used = :last_used
        WHERE user_id = :user_id AND key_name = 'schwab'
    """, {
        "user_id": current_user.id,
        "access_token": client.tokens.access_token,
        "refresh_token": client.tokens.refresh_token,
        "last_used": datetime.utcnow()
    })

    return {"message": "Schwab account linked successfully"}

@router.get("/schwab/account-status")
async def get_schwab_account_status(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    credentials = await db.fetch_one(
        "SELECT * FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
        {"user_id": current_user.id}
    )

    if credentials:
        return {
            "is_linked": True,
            "last_used": credentials['last_used']
        }
    else:
        return {"is_linked": False}

@router.delete("/schwab/unlink-account")
async def unlink_schwab_account(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    result = await db.execute(
        "DELETE FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
        {"user_id": current_user.id}
    )

    if result == 0:
        raise HTTPException(status_code=404, detail="No Schwab account linked")

    return {"message": "Schwab account unlinked successfully"}

@router.post("/execute-trade")
async def execute_trade(
    order: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        credentials = await schwab_service.get_schwab_credentials(current_user.id)
        client = schwab_service.initialize_schwab_client(
            current_user.id,
            credentials['api_key'],
            credentials['api_secret'],
            credentials['callback_url']
        )
        result = await schwab_service.execute_trade(client, credentials['account_hash'], order)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))