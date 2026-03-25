import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId

from app.core.config import settings
from app.db.mongodb import get_client
from app.schemas.sop import SOPCropData, SOPDataRequest, SOPDataResponse


def _serialize_mongo_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_serialize_mongo_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_mongo_value(val) for key, val in value.items()}
    return value


def _normalize(value: str) -> str:
    return value.strip().lower()


async def get_sop_data(payload: SOPDataRequest) -> SOPDataResponse:
    mongo_client = get_client()
    sop_collection = mongo_client[settings.sop_db_name][settings.sop_collection_name]

    requested_names = payload.crop_names
    patterns = [
        {"Crop_name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
        for name in requested_names
    ]
    docs = (
        await sop_collection.find({"$or": patterns}).to_list(length=len(requested_names))
        if patterns
        else []
    )

    found_map: dict[str, dict[str, Any]] = {}
    for doc in docs:
        crop_name = str(doc.get("Crop_name", "")).strip()
        if not crop_name:
            continue
        normalized = _normalize(crop_name)
        if normalized not in found_map:
            found_map[normalized] = _serialize_mongo_value(doc)

    found_crops: list[SOPCropData] = []
    missing_crops: list[str] = []
    for requested in requested_names:
        normalized = _normalize(requested)
        doc = found_map.get(normalized)
        if not doc:
            missing_crops.append(requested)
            continue
        doc_without_id = {k: v for k, v in doc.items() if k != "_id"}
        crop_name = str(doc_without_id.get("Crop_name", requested))
        found_crops.append(SOPCropData(crop_name=crop_name, data=doc_without_id))

    return SOPDataResponse(
        user_id=payload.user_id,
        total_requested=len(requested_names),
        total_found=len(found_crops),
        found_crops=found_crops,
        missing_crops=missing_crops,
    )

