from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import get_current_user_id
from app.schemas.planner import (
    PlannerDeviceUpdateRequest,
    PlannerDeviceUpdateResponse,
    PlannerRequest,
    PlannerResponse,
    SinchaiPlannerResponse,
    UpdateSinchaiPlannerRequest,
    UpdateSinchaiPlannerResponse,
)
from app.services.planner_service import (
    get_planner_devices,
    get_sinchai_planner,
    update_sinchai_planner,
    update_planner_device,
)


router = APIRouter(tags=["Planner"])


@router.post("/planner", response_model=PlannerResponse)
async def planner(
    payload: PlannerRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> PlannerResponse:
    return await get_planner_devices(payload=payload, token_user_id=token_user_id)


@router.post("/planner/update-device", response_model=PlannerDeviceUpdateResponse)
async def planner_update_device(
    payload: PlannerDeviceUpdateRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> PlannerDeviceUpdateResponse:
    return await update_planner_device(payload=payload, token_user_id=token_user_id)


@router.get("/get_sinchai_planer", response_model=SinchaiPlannerResponse)
async def get_sinchai_planer(
    token_type: str = Query(default="bearer"),
    user_id: str = Query(..., min_length=1),
    section: str = Query(default="user_sinchai_planner", min_length=1),
    token_user_id: str = Depends(get_current_user_id),
) -> SinchaiPlannerResponse:
    return await get_sinchai_planner(
        token_type=token_type,
        user_id=user_id,
        section=section,
        token_user_id=token_user_id,
    )


@router.post("/update_sinchai_planer", response_model=UpdateSinchaiPlannerResponse)
async def update_sinchai_planer(
    payload: UpdateSinchaiPlannerRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> UpdateSinchaiPlannerResponse:
    return await update_sinchai_planner(payload=payload, token_user_id=token_user_id)
