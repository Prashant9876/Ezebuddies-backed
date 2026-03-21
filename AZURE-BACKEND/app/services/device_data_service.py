from datetime import date, datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.db.mongodb import get_client
from app.models.user import User
from app.schemas.device_data import UserDevicesDataResponse


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


async def get_user_devices_data(user_id: str) -> UserDevicesDataResponse:
    mongo_client = get_client()
    users_collection = mongo_client[settings.login_db_name][settings.login_collection]
    user_doc = await users_collection.find_one({"$or": [{"user_id": user_id}, {"_id": user_id}]})

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        user = User.from_mongo(user_doc)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile data is invalid",
        )
    auth_user_id = user.user_id or user.id
    source_collection = mongo_client[settings.realtime_db_name][auth_user_id]
    cursor = source_collection.find({}).sort("_id", -1)
    if settings.device_data_fetch_limit > 0:
        cursor = cursor.limit(settings.device_data_fetch_limit)
        all_records = await cursor.to_list(length=settings.device_data_fetch_limit)
    else:
        all_records = []
        async for doc in cursor:
            all_records.append(doc)
    serialized_records = [_serialize_mongo_value(record) for record in all_records]

    return UserDevicesDataResponse(
        user_id=auth_user_id,
        source_database=settings.realtime_db_name,
        source_collection=auth_user_id,
        total_records=len(serialized_records),
        records=serialized_records,
    )
