from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.api.auth import get_current_user
from app.services import schwab_service
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class SchwabCredentials(BaseModel):
    api_key: str
    api_secret: str
    access_token: str
    refresh_token: str

@router.post("/schwab/link-account")
async def link_schwab_account(
    credentials: SchwabCredentials,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    # Check if user already has Schwab credentials
    existing_credentials = await db.fetch_one(
        "SELECT * FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
        {"user_id": current_user.id}
    )

    if existing_credentials:
        # Update existing credentials
        await db.execute("""
            UPDATE api_keys 
            SET api_key = :api_key, api_secret = :api_secret, 
                access_token = :access_token, refresh_token = :refresh_token,
                last_used = :last_used
            WHERE user_id = :user_id AND key_name = 'schwab'
        """, {
            "user_id": current_user.id,
            "api_key": credentials.api_key,
            "api_secret": credentials.api_secret,
            "access_token": credentials.access_token,
            "refresh_token": credentials.refresh_token,
            "last_used": datetime.utcnow()
        })
    else:
        # Insert new credentials
        await db.execute("""
            INSERT INTO api_keys (user_id, key_name, api_key, api_secret, access_token, refresh_token, last_used)
            VALUES (:user_id, 'schwab', :api_key, :api_secret, :access_token, :refresh_token, :last_used)
        """, {
            "user_id": current_user.id,
            "api_key": credentials.api_key,
            "api_secret": credentials.api_secret,
            "access_token": credentials.access_token,
            "refresh_token": credentials.refresh_token,
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