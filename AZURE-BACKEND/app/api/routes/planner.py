from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user_id
from app.schemas.planner import (
    PlannerDeviceUpdateRequest,
    PlannerDeviceUpdateResponse,
    PlannerRequest,
    PlannerResponse,
)
from app.services.planner_service import get_planner_devices, update_planner_device


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
