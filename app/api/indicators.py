# app/api/indicators.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.indicator import Indicator, IndicatorCreate
from app.db.database import get_db
from app.api.auth import get_current_user

router = APIRouter()

@router.post("/indicators", response_model=Indicator)
async def create_indicator(indicator: IndicatorCreate, current_user = Depends(get_current_user), db = Depends(get_db)):
    new_indicator = indicator.dict()
    result = await db.execute(
        """
        INSERT INTO indicators (name, description, parameters)
        VALUES (:name, :description, :parameters)
        RETURNING *
        """,
        new_indicator
    )
    return Indicator(**result)

@router.get("/indicators", response_model=List[Indicator])
async def get_indicators(db = Depends(get_db)):
    results = await db.fetch_all("SELECT * FROM indicators")
    return [Indicator(**result) for result in results]

@router.get("/indicators/{indicator_id}", response_model=Indicator)
async def get_indicator(indicator_id: int, db = Depends(get_db)):
    result = await db.fetch_one("SELECT * FROM indicators WHERE id = :id", {"id": indicator_id})
    if result is None:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return Indicator(**result)