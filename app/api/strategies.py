# app/api/strategies.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.models.strategy import Strategy, StrategyCreate, StrategyComponent
from app.db.database import get_db
from app.api.auth import get_current_user
from datetime import datetime, timezone
from app.utils.json_encoder import json_serializer

router = APIRouter()

@router.post("/strategies", response_model=Strategy)
async def create_strategy(strategy: StrategyCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    try:
        # Convert strategy to dict with serializable dates
        strategy_dict = strategy.model_dump()
        current_time = datetime.now(timezone.utc)
        
        # Prepare the strategy data
        db_strategy = {
            "name": strategy_dict['name'],
            "description": strategy_dict['description'],
            "is_active": strategy_dict['is_active'],
            "user_id": current_user.user_id,
            "asset_filters": json_serializer(strategy_dict['asset_filters']),
            "additional_config": json_serializer(strategy_dict.get('additional_config', {})),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat()
        }
        
        # Insert strategy
        strategy_result = db.table("strategies").insert(db_strategy).execute()
        
        if not strategy_result.data:
            raise HTTPException(status_code=500, detail="Failed to create strategy")
            
        strategy_id = strategy_result.data[0]['id']
        components = []
        
        # Insert components
        for component in strategy_dict['components']:
            db_component = {
                "strategy_id": strategy_id,
                "component_type": component['component_type'],
                "conditions": json_serializer(component.get('conditions', [])),
                "exit_conditions": json_serializer(component.get('exit_conditions', [])),
                "parameters": json_serializer(component.get('parameters', {}))
            }
            
            component_result = db.table("strategy_components").insert(db_component).execute()
            if component_result.data:
                components.append(StrategyComponent(**{
                    **component,
                    'id': component_result.data[0]['id']
                }))
        
        # Construct the complete strategy object
        created_strategy = Strategy(
            id=strategy_id,
            user_id=current_user.user_id,
            name=strategy_dict['name'],
            description=strategy_dict['description'],
            is_active=strategy_dict['is_active'],
            asset_filters=strategy_dict['asset_filters'],
            components=components,
            additional_config=strategy_dict.get('additional_config', {}),
            created_at=current_time,
            updated_at=current_time
        )
        
        return created_strategy
        
    except Exception as e:
        print(f"Error creating strategy: {str(e)}")
        print(f"Strategy data: {strategy_dict}")
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