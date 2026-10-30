from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.core.rate_limit import limiter
from app.database.mongo import get_db
from app.monitoring.checker import check_monitor, new_client
from app.schemas.incident import IncidentOut
from app.schemas.monitor import (ActiveIn, ChartPoint, CheckResultOut, MonitorIn, MonitorOut, Page, StatsOut)
from app.security.deps import get_current_user
from app.services import incidents as incident_service
from app.services import monitors as monitor_service
from app.services import results as result_service
from app.services.common import utcnow

router = APIRouter(prefix="/monitors", tags=["monitors"])
RangeName = Literal["1h", "24h", "7d", "30d"]


@router.post("", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def create_monitor(data: MonitorIn, user=Depends(get_current_user), db=Depends(get_db)):
    return monitor_service.monitor_out(await monitor_service.create(db, user, data))


@router.get("", response_model=Page)
async def list_monitors(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Literal["UP", "DOWN", "PENDING"] | None = Query(None, alias="status"),
    search: str | None = Query(None, max_length=100),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    return await monitor_service.list_page(db, user, page, limit, status_filter, search)


@router.get("/{monitor_id}", response_model=MonitorOut)
async def get_monitor(monitor_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return monitor_service.monitor_out(await monitor_service.get_owned(db, user, monitor_id))


@router.put("/{monitor_id}", response_model=MonitorOut)
async def update_monitor(monitor_id: str, data: MonitorIn, user=Depends(get_current_user), db=Depends(get_db)):
    return monitor_service.monitor_out(await monitor_service.update(db, user, monitor_id, data))


@router.patch("/{monitor_id}/active", response_model=MonitorOut)
async def toggle_active(monitor_id: str, data: ActiveIn, user=Depends(get_current_user), db=Depends(get_db)):
    return monitor_service.monitor_out(await monitor_service.set_active(db, user, monitor_id, data.is_active))


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(monitor_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    await monitor_service.delete(db, user, monitor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{monitor_id}/check", response_model=CheckResultOut)
@limiter.limit("10/minute")
async def manual_check(request: Request, monitor_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    """Runs ONE check inside the request (bounded by the monitor's timeout, max 30 s)."""
    monitor = await monitor_service.get_owned(db, user, monitor_id)
    async with new_client() as client:
        outcome = await check_monitor(db, monitor, client)
    return CheckResultOut(
        id="manual",
        monitor_id=str(monitor["_id"]),
        status=outcome.status,
        http_status_code=outcome.http_status_code,
        response_time_ms=outcome.response_time_ms,
        error_message=outcome.error_message,
        checked_at=outcome.checked_at,
    )


@router.get("/{monitor_id}/results", response_model=Page)
async def monitor_results(
    monitor_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Literal["UP", "DOWN"] | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None, alias="from"),
    date_to: datetime | None = Query(None, alias="to"),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    m = await monitor_service.get_owned(db, user, monitor_id)
    return await result_service.history(db, m["_id"], page, limit, status_filter, date_from, date_to)


@router.get("/{monitor_id}/stats", response_model=StatsOut)
async def monitor_stats(monitor_id: str, range: RangeName = "24h", user=Depends(get_current_user), db=Depends(get_db)):
    m = await monitor_service.get_owned(db, user, monitor_id)
    return await result_service.stats(db, [m["_id"]], range)


@router.get("/{monitor_id}/chart", response_model=list[ChartPoint])
async def monitor_chart(monitor_id: str, range: RangeName = "24h", user=Depends(get_current_user), db=Depends(get_db)):
    m = await monitor_service.get_owned(db, user, monitor_id)
    return await result_service.chart(db, [m["_id"]], range)


@router.get("/{monitor_id}/incidents", response_model=Page)
async def monitor_incidents(
    monitor_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    m = await monitor_service.get_owned(db, user, monitor_id)
    return await incident_service.list_page(db, user, page, limit, monitor_id=str(m["_id"]))
