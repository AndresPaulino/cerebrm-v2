# app/api/strategies.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.strategy import Strategy, StrategyCreate, StrategyComponent
from app.db.database import get_db
from app.api.auth import get_current_user
from datetime import datetime, timezone

router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.strategy import Strategy, StrategyCreate, StrategyComponent
from app.db.database import get_db
from app.api.auth import get_current_user
from datetime import datetime, timezone

router = APIRouter()

@router.post("/strategies", response_model=Strategy)
async def create_strategy(strategy: StrategyCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    try:
        new_strategy = strategy.dict()
        new_strategy['user_id'] = current_user.user_id
        new_strategy['created_at'] = datetime.now(timezone.utc)
        new_strategy['updated_at'] = datetime.now(timezone.utc)
        
        # Insert the strategy
        strategy_result = db.table("strategies").insert({
            "name": new_strategy['name'],
            "description": new_strategy['description'],
            "is_active": new_strategy['is_active'],
            "user_id": new_strategy['user_id'],
            "asset_filters": new_strategy['asset_filters'],
            "additional_config": new_strategy['additional_config'],
            "created_at": new_strategy['created_at'],
            "updated_at": new_strategy['updated_at']
        }).execute()
        
        strategy_id = strategy_result.data[0]['id']
        components = []
        
        # Insert the components
        for component in new_strategy['components']:
            component_result = db.table("strategy_components").insert({
                "strategy_id": strategy_id,
                "component_type": component['component_type'],
                "conditions": component.get('conditions', []),
                "exit_conditions": component.get('exit_conditions', []),
                "parameters": component['parameters']
            }).execute()
            components.append(StrategyComponent(**component_result.data[0]))
    
        return Strategy(**new_strategy, id=strategy_id, components=components)
    except Exception as e:
        print(f"Error creating strategy: {str(e)}")
        print(f"Strategy data: {new_strategy}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating strategy: {str(e)}")

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

@router.put("/strategies/{strategy_id}", response_model=Strategy)
async def update_strategy(strategy_id: int, strategy: StrategyCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    existing = await get_strategy(strategy_id, current_user, db)
    if not existing:
        raise HTTPException(status_code=404, detail="Strategy not found")

    update_data = strategy.dict(exclude_unset=True)
    update_data['updated_at'] = datetime.utcnow()

    async with db.transaction():
        await db.execute(
            """
            UPDATE strategies
            SET name = :name, description = :description, is_active = :is_active,
                asset_filters = :asset_filters, additional_config = :additional_config, updated_at = :updated_at
            WHERE id = :id
            """,
            {**update_data, 'id': strategy_id}
        )

        # Delete existing components and insert new ones
        await db.execute("DELETE FROM strategy_components WHERE strategy_id = :strategy_id", {"strategy_id": strategy_id})
        
        for component in update_data['components']:
            await db.execute(
                """
                INSERT INTO strategy_components (strategy_id, component_type, conditions, exit_conditions, parameters)
                VALUES (:strategy_id, :component_type, :conditions, :exit_conditions, :parameters)
                """,
                {**component.dict(), 'strategy_id': strategy_id}
            )

    return await get_strategy(strategy_id, current_user, db)

@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user = Depends(get_current_user), db = Depends(get_db)):
    strategy = await get_strategy(strategy_id, current_user, db)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    async with db.transaction():
        await db.execute("DELETE FROM strategy_components WHERE strategy_id = :strategy_id", {"strategy_id": strategy_id})
        await db.execute("DELETE FROM strategies WHERE id = :id", {"id": strategy_id})

    return {"message": "Strategy deleted successfully"}

@router.get("/strategy-templates")
async def get_strategy_templates():
    templates = [
        {
            "name": "Moving Average Crossover",
            "description": "Buy when fast MA crosses above slow MA, sell when it crosses below",
            "components": [
                {
                    "component_type": "entry",
                    "conditions": [
                        {
                            "type": "technical_indicator",
                            "indicator": "SMA",
                            "comparison": "crosses_above",
                            "value": {"fast_period": 10, "slow_period": 50}
                        }
                    ],
                    "parameters": {"action": "buy"}
                },
                {
                    "component_type": "exit",
                    "conditions": [
                        {
                            "type": "technical_indicator",
                            "indicator": "SMA",
                            "comparison": "crosses_below",
                            "value": {"fast_period": 10, "slow_period": 50}
                        }
                    ],
                    "parameters": {"action": "sell"}
                }
            ]
        },
        {
            "name": "RSI Oversold/Overbought",
            "description": "Buy when RSI is oversold, sell when overbought",
            "components": [
                {
                    "component_type": "entry",
                    "conditions": [
                        {
                            "type": "technical_indicator",
                            "indicator": "RSI",
                            "comparison": "less_than",
                            "value": 30
                        }
                    ],
                    "parameters": {"action": "buy"}
                },
                {
                    "component_type": "exit",
                    "conditions": [
                        {
                            "type": "technical_indicator",
                            "indicator": "RSI",
                            "comparison": "greater_than",
                            "value": 70
                        }
                    ],
                    "parameters": {"action": "sell"}
                }
            ]
        }
    ]
    return templates