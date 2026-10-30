from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.database.mongo import get_db
from app.schemas.incident import IncidentOut
from app.schemas.monitor import Page
from app.security.deps import get_current_user
from app.services import incidents as incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=Page)
async def list_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Literal["OPEN", "RESOLVED"] | None = None,
    monitor_id: str | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    return await incident_service.list_page(db, user, page, limit, status, monitor_id)


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return await incident_service.get_owned(db, user, incident_id)
