# app/api/strategies.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.strategy import Strategy, StrategyCreate, StrategyComponent
from app.db.database import get_db
from app.api.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/strategies", response_model=Strategy)
async def create_strategy(strategy: StrategyCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    new_strategy = strategy.dict()
    new_strategy['user_id'] = current_user.id
    new_strategy['created_at'] = datetime.utcnow()
    new_strategy['updated_at'] = datetime.utcnow()
    
    async with db.transaction():
        strategy_result = await db.fetch_one(
            """
            INSERT INTO strategies (name, description, is_active, user_id, additional_config, created_at, updated_at)
            VALUES (:name, :description, :is_active, :user_id, :additional_config, :created_at, :updated_at)
            RETURNING *
            """,
            {k: v for k, v in new_strategy.items() if k != 'components'}
        )
        
        strategy_id = strategy_result['id']
        components = []
        
        for component in new_strategy['components']:
            component_result = await db.fetch_one(
                """
                INSERT INTO strategy_components (strategy_id, component_type, parameters)
                VALUES (:strategy_id, :component_type, :parameters)
                RETURNING *
                """,
                {**component.dict(), 'strategy_id': strategy_id}
            )
            components.append(StrategyComponent(**component_result))
    
    return Strategy(**strategy_result, components=components)

@router.get("/strategies", response_model=List[Strategy])
async def get_strategies(current_user = Depends(get_current_user), db = Depends(get_db)):
    strategies = await db.fetch_all(
        "SELECT * FROM strategies WHERE user_id = :user_id",
        {"user_id": current_user.id}
    )
    
    result = []
    for strategy in strategies:
        components = await db.fetch_all(
            "SELECT * FROM strategy_components WHERE strategy_id = :strategy_id",
            {"strategy_id": strategy['id']}
        )
        result.append(Strategy(**strategy, components=[StrategyComponent(**c) for c in components]))
    
    return result

@router.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: int, current_user = Depends(get_current_user), db = Depends(get_db)):
    strategy = await db.fetch_one(
        "SELECT * FROM strategies WHERE id = :id AND user_id = :user_id",
        {"id": strategy_id, "user_id": current_user.id}
    )
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    components = await db.fetch_all(
        "SELECT * FROM strategy_components WHERE strategy_id = :strategy_id",
        {"strategy_id": strategy_id}
    )
    
    return Strategy(**strategy, components=[StrategyComponent(**c) for c in components])

# Add more endpoints for updating and deleting strategies