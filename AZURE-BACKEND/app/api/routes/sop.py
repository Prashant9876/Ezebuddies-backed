from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import get_current_user_id
from app.schemas.sop import SOPDataRequest, SOPDataResponse
from app.services.sop_service import get_sop_data


router = APIRouter(tags=["SOP"])


@router.post("/SOP_data", response_model=SOPDataResponse)
async def sop_data(
    payload: SOPDataRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> SOPDataResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own SOP data",
        )
    return await get_sop_data(payload)

