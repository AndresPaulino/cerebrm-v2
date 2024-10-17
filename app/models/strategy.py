# app/models/strategy.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class StrategyComponentBase(BaseModel):
    component_type: str  # 'indicator', 'entry', 'exit', 'position_sizing', 'risk_management'
    parameters: Dict[str, Any]

class StrategyComponent(StrategyComponentBase):
    id: int

class StrategyBase(BaseModel):
    name: str
    description: str
    is_active: bool = True
    components: List[StrategyComponentBase]
    additional_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

class StrategyCreate(StrategyBase):
    pass

class Strategy(StrategyBase):
    id: int
    user_id: int
    components: List[StrategyComponent]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True