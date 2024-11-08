# app/models/indicator.py
from pydantic import BaseModel
from typing import Dict, Any

class IndicatorBase(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class IndicatorCreate(IndicatorBase):
    pass

class Indicator(IndicatorBase):
    id: int

    class Config:
        from_attributes = True