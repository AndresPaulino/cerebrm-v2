# app/models/strategy.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class AssetFilter(BaseModel):
    type: str  # e.g., "symbol", "sector", "market_cap", "custom_list"
    value: Any

class Condition(BaseModel):
    type: str  # e.g., "price_change", "technical_indicator", "time"
    indicator: Optional[str] = None  # e.g., "SMA", "EMA", "RSI"
    comparison: str  # e.g., "greater_than", "less_than", "crosses_above"
    value: Any

class ExitCondition(BaseModel):
    type: str  # e.g., "take_profit", "stop_loss", "trailing_stop", "time_based"
    value: Any

class StrategyComponentBase(BaseModel):
    component_type: str  # 'entry', 'exit'
    conditions: Optional[List[Condition]] = []
    exit_conditions: Optional[List[ExitCondition]] = []
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
        from_attributes = True  # This replaces orm_mode = True in Pydantic v2