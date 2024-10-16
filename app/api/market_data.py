from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging
from app.services.polygon_service import polygon_ws
from app.api.auth import get_current_user_bearer
from app.models.user import User
from app.db.database import get_db
from app.core.cache import get_cached_data, set_cached_data
from typing import List
from datetime import datetime, timedelta
import json

router = APIRouter()
logger = logging.getLogger(__name__)

class SymbolList(BaseModel):
    symbols: List[str]

@router.post("/market-data/subscribe")
async def subscribe_to_symbols(symbol_list: SymbolList, current_user: User = Depends(get_current_user_bearer)):
    try:
        if polygon_ws is None:
            logger.error("polygon_ws is None")
            raise HTTPException(status_code=500, detail="WebSocket not initialized")
        
        if polygon_ws.connection is None:
            logger.error("polygon_ws.connection is None")
            raise HTTPException(status_code=500, detail="WebSocket connection not established")
        
        logger.info(f"Attempting to subscribe to symbols: {symbol_list.symbols}")
        await polygon_ws.subscribe(symbol_list.symbols)
        return {"message": f"Subscribed to symbols: {', '.join(symbol_list.symbols)}"}
    except Exception as e:
        logger.error(f"Error in subscribe_to_symbols: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-data/unsubscribe")
async def unsubscribe_from_symbols(symbols: List[str], current_user: User = Depends(get_current_user_bearer)):
    try:
        await polygon_ws.unsubscribe(symbols)
        return {"message": f"Unsubscribed from symbols: {', '.join(symbols)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/subscribed")
async def get_subscribed_symbols(current_user: User = Depends(get_current_user_bearer)):
    return {"subscribed_symbols": list(polygon_ws.subscribed_symbols)}

@router.get("/market-data/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: datetime,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user_bearer),
    db = Depends(get_db)
):
    if end_date is None:
        end_date = datetime.utcnow()

    query = """
    SELECT time, open, high, low, close, volume
    FROM market_data
    WHERE symbol = :symbol AND time BETWEEN :start_date AND :end_date
    ORDER BY time ASC
    """
    results = await db.fetch_all(query, {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date
    })

    return [dict(row) for row in results]

@router.get("/market-data/latest/{symbol}")
async def get_latest_data(
    symbol: str,
    current_user: User = Depends(get_current_user_bearer),
    db = Depends(get_db)
):
    cache_key = f"latest_data:{symbol}"
    cached_data = await get_cached_data(cache_key)

    if cached_data:
        return json.loads(cached_data)

    query = """
    SELECT time, open, high, low, close, volume
    FROM market_data
    WHERE symbol = :symbol
    ORDER BY time DESC
    LIMIT 1
    """
    result = await db.fetch_one(query, {"symbol": symbol})

    if result is None:
        raise HTTPException(status_code=404, detail="No data found for the given symbol")

    data = dict(result)
    await set_cached_data(cache_key, json.dumps(data), expiration=60)  # Cache for 1 minute

    return data