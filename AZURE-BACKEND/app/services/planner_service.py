from typing import Any, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.db.mongodb import get_client
from app.schemas.planner import PlannerRequest, PlannerResponse


def _candidate_collection_names(section: str) -> list[str]:
    names = [section, section.strip(), section.replace(" ", "_"), section.replace(" ", "")]
    unique_names: list[str] = []
    for name in names:
        if name and name not in unique_names:
            unique_names.append(name)
    return unique_names


async def _find_user_plan_doc(section: str, user_id: str) -> Optional[dict[str, Any]]:
    mongo_client = get_client()
    section_db = mongo_client[settings.login_db_name]
    for collection_name in _candidate_collection_names(section):
        doc = await section_db[collection_name].find_one({"user_id": user_id})
        if doc:
            return doc
    return None


async def get_planner_devices(
    payload: PlannerRequest, token_user_id: str
) -> PlannerResponse:
    if payload.token_type.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="token_type must be bearer",
        )

    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own planner data",
        )

    plan_doc = await _find_user_plan_doc(section=payload.section, user_id=payload.user_id)
    if not plan_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planner data not found for this user in requested section",
        )

    devices = plan_doc.get("devices")
    if not isinstance(devices, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Planner data format is invalid: devices is missing",
        )

    return PlannerResponse(user_id=payload.user_id, devices=devices)
