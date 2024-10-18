# app/models/strategy.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class AssetFilter(BaseModel):
    type: str  # e.g., "sector", "market_cap", "custom_list"
    value: Any

class Condition(BaseModel):
    type: str  # e.g., "technical_indicator", "price", "time"
    indicator: Optional[str]  # e.g., "SMA", "EMA", "RSI"
    comparison: str  # e.g., "greater_than", "less_than", "equal_to"
    value: Any
    time_restriction: Optional[Dict[str, Any]]  # e.g., {"start": "09:30", "end": "16:00"}

class ExitCondition(BaseModel):
    type: str  # e.g., "take_profit", "stop_loss", "trailing_stop", "time_based"
    value: Any

class StrategyComponentBase(BaseModel):
    component_type: str  # 'entry', 'exit', 'position_sizing', 'risk_management'
    conditions: List[Condition]
    exit_conditions: List[ExitCondition]
    parameters: Dict[str, Any]

class StrategyComponent(StrategyComponentBase):
    id: int

class StrategyBase(BaseModel):
    name: str
    description: str
    is_active: bool = True
    asset_filters: List[AssetFilter]
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