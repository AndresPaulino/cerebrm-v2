from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.strategy import Strategy, StrategyCreate, StrategyUpdate, StrategyCondition
from app.services.schwab_service import execute_trade
from app.api.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/strategies", response_model=Strategy)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    new_strategy = {
        "name": strategy.name,
        "description": strategy.description,
        "is_active": strategy.is_active,
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "last_modified": datetime.utcnow()
    }
    result = db.table("strategies").insert(new_strategy).execute()
    strategy_id = result.data[0]['id']

    conditions = [
        {
            "strategy_id": strategy_id,
            "asset_id": condition.asset_id,
            "condition_type": condition.condition_type,
            "parameter": condition.parameter,
            "action": condition.action,
            "created_at": datetime.utcnow()
        }
        for condition in strategy.conditions
    ]
    db.table("strategy_conditions").insert(conditions).execute()

    return get_strategy(strategy_id, current_user, db)

@router.get("/strategies", response_model=List[Strategy])
async def get_strategies(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    strategies = db.table("strategies").select("*").eq("user_id", current_user.id).execute()
    strategy_list = []
    for strategy in strategies.data:
        conditions = db.table("strategy_conditions").select("*").eq("strategy_id", strategy['id']).execute()
        strategy['conditions'] = [StrategyCondition(**condition) for condition in conditions.data]
        strategy_list.append(Strategy(**strategy))
    return strategy_list

@router.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    strategy = db.table("strategies").select("*").eq("id", strategy_id).eq("user_id", current_user.id).execute()
    if not strategy.data:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    conditions = db.table("strategy_conditions").select("*").eq("strategy_id", strategy_id).execute()
    strategy.data[0]['conditions'] = [StrategyCondition(**condition) for condition in conditions.data]
    return Strategy(**strategy.data[0])

@router.post("/strategies/{strategy_id}/execute")
async def execute_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    strategy = await db.fetch_one(
        "SELECT * FROM strategies WHERE strategy_id = :strategy_id AND user_id = :user_id",
        {"strategy_id": strategy_id, "user_id": current_user.id}
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Here you would evaluate the strategy and generate trade signals
    # This is a placeholder for the actual implementation
    trade_details = {
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 10,
        "price": 150.00
    }

    try:
        result = await execute_trade(current_user.id, trade_details)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/strategies/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    existing_strategy = db.table("strategies").select("*").eq("id", strategy_id).eq("user_id", current_user.id).execute()
    if not existing_strategy.data:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    updated_strategy = {
        "name": strategy_update.name,
        "description": strategy_update.description,
        "is_active": strategy_update.is_active,
        "last_modified": datetime.utcnow()
    }
    db.table("strategies").update(updated_strategy).eq("id", strategy_id).execute()

    if strategy_update.conditions is not None:
        db.table("strategy_conditions").delete().eq("strategy_id", strategy_id).execute()
        new_conditions = [
            {
                "strategy_id": strategy_id,
                "asset_id": condition.asset_id,
                "condition_type": condition.condition_type,
                "parameter": condition.parameter,
                "action": condition.action,
                "created_at": datetime.utcnow()
            }
            for condition in strategy_update.conditions
        ]
        db.table("strategy_conditions").insert(new_conditions).execute()

    return get_strategy(strategy_id, current_user, db)

@router.delete("/strategies/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    strategy = db.table("strategies").select("*").eq("id", strategy_id).eq("user_id", current_user.id).execute()
    if not strategy.data:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.table("strategy_conditions").delete().eq("strategy_id", strategy_id).execute()
    db.table("strategies").delete().eq("id", strategy_id).execute()
    return {"detail": "Strategy deleted successfully"}