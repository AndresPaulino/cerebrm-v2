from pydantic import BaseModel, Json
from typing import List, Optional
from datetime import datetime

class StrategyCondition(BaseModel):
    asset_id: int
    condition_type: str
    parameter: Json
    action: str

class StrategyBase(BaseModel):
    name: str
    description: str
    is_active: bool = True

class StrategyCreate(StrategyBase):
    conditions: List[StrategyCondition]

class StrategyUpdate(StrategyBase):
    conditions: Optional[List[StrategyCondition]]

class Strategy(StrategyBase):
    id: int
    user_id: int
    created_at: datetime
    last_modified: datetime
    conditions: List[StrategyCondition]

    class Config:
        orm_mode = True