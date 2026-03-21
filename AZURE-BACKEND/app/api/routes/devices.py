from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import get_current_user_id
from app.schemas.device_data import UserDevicesDataResponse
from app.services.device_data_service import get_user_devices_data


router = APIRouter(prefix="/users", tags=["Devices"])


@router.get("/{user_id}/devices/data", response_model=UserDevicesDataResponse)
async def fetch_user_devices_data(
    user_id: str, token_user_id: str = Depends(get_current_user_id)
) -> UserDevicesDataResponse:
    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own devices data",
        )
    return await get_user_devices_data(user_id=user_id)
