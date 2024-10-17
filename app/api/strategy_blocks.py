# app/api/strategy_blocks.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.strategy_block import StrategyBlock, StrategyBlockCreate
from app.db.database import get_db
from app.api.auth import get_current_user

router = APIRouter()

@router.post("/strategy-blocks", response_model=StrategyBlock)
async def create_strategy_block(block: StrategyBlockCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    new_block = block.dict()
    result = await db.execute(
        """
        INSERT INTO strategy_blocks (name, block_type, parameters)
        VALUES (:name, :block_type, :parameters)
        RETURNING *
        """,
        new_block
    )
    return StrategyBlock(**result)

@router.get("/strategy-blocks", response_model=List[StrategyBlock])
async def get_strategy_blocks(db = Depends(get_db)):
    results = await db.fetch_all("SELECT * FROM strategy_blocks")
    return [StrategyBlock(**result) for result in results]

@router.get("/strategy-blocks/{block_id}", response_model=StrategyBlock)
async def get_strategy_block(block_id: int, db = Depends(get_db)):
    result = await db.fetch_one("SELECT * FROM strategy_blocks WHERE id = :id", {"id": block_id})
    if result is None:
        raise HTTPException(status_code=404, detail="Strategy block not found")
    return StrategyBlock(**result)