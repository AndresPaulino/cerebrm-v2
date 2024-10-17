# app/models/strategy_block.py
from pydantic import BaseModel
from typing import Dict, Any

class StrategyBlockBase(BaseModel):
    name: str
    block_type: str  # 'entry', 'exit', 'position_sizing', 'risk_management'
    parameters: Dict[str, Any]

class StrategyBlockCreate(StrategyBlockBase):
    pass

class StrategyBlock(StrategyBlockBase):
    id: int

    class Config:
        orm_mode = True