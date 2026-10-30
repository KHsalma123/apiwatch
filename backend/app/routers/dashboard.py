from typing import Literal

from fastapi import APIRouter, Depends

from app.database.mongo import get_db
from app.security.deps import get_current_user
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user=Depends(get_current_user), db=Depends(get_db)):
    return await dashboard_service.summary(db, user)


@router.get("/charts")
async def charts(range: Literal["1h", "24h", "7d", "30d"] = "24h", user=Depends(get_current_user), db=Depends(get_db)):
    return await dashboard_service.charts(db, user, range)
