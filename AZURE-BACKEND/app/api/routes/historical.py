from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user_id
from app.schemas.historical import HistoricalDataRequest, HistoricalDataResponse
from app.services.historical_service import get_historical_data


router = APIRouter(tags=["Historical Data"])


@router.post("/historical_data", response_model=HistoricalDataResponse)
async def historical_data(
    payload: HistoricalDataRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> HistoricalDataResponse:
    return await get_historical_data(payload=payload, token_user_id=token_user_id)

