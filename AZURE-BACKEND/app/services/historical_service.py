from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.db.mongodb import get_client
from app.schemas.historical import (
    HistoricalDataPoint,
    HistoricalDataRequest,
    HistoricalDataResponse,
)


def _determine_bucket_minutes(time_range_days: float) -> int:
    if time_range_days >= 3:
        return 120
    if time_range_days >= 0.5:
        return 60
    return 5


def _floor_to_bucket(dt: datetime, bucket_minutes: int) -> datetime:
    epoch = int(dt.timestamp())
    bucket_seconds = bucket_minutes * 60
    floored = (epoch // bucket_seconds) * bucket_seconds
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _build_payload_from_bucket(
    docs: list[dict[str, Any]], device_name: str
) -> dict[str, Any]:
    numeric_values: dict[str, list[float]] = defaultdict(list)
    fallback_values: dict[str, Any] = {}
    skip_keys = {"_id", "timestamp", "ts"}

    for doc in docs:
        for key, value in doc.items():
            if key in skip_keys:
                continue
            if isinstance(value, bool):
                fallback_values[key] = value
                continue
            if isinstance(value, (int, float)):
                numeric_values[key].append(float(value))
            else:
                fallback_values[key] = value

    payload: dict[str, Any] = {}
    if device_name == "Enviroment_Intel":
        target_keys = {"CO2", "Etemp", "Humidity"}
        for key in target_keys:
            values = numeric_values.get(key, [])
            if values:
                payload[key] = round(sum(values) / len(values), 3)
    else:
        for key, values in numeric_values.items():
            if values:
                payload[key] = round(sum(values) / len(values), 3)

    payload.update(fallback_values)
    return payload


async def get_historical_data(
    payload: HistoricalDataRequest, token_user_id: str
) -> HistoricalDataResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own historical data",
        )

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=payload.time_range.value)
    bucket_minutes = _determine_bucket_minutes(payload.time_range.value)

    mongo_client = get_client()
    collection = mongo_client[settings.historical_db_name][
        settings.historical_collection_name
    ]

    pipeline = [
        {"$match": {"$or": [{"Device_Id": payload.device_id}, {"device_id": payload.device_id}]}},
        {
            "$addFields": {
                "ts": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$eq": [{"$type": "$timestamp"}, "date"]},
                                "then": "$timestamp",
                            },
                            {
                                "case": {"$eq": [{"$type": "$timestamp"}, "string"]},
                                "then": {
                                    "$dateFromString": {
                                        "dateString": "$timestamp",
                                        "onError": None,
                                        "onNull": None,
                                    }
                                },
                            },
                        ],
                        "default": None,
                    }
                }
            }
        },
        {"$match": {"ts": {"$ne": None, "$gte": start_time, "$lte": now}}},
        {"$sort": {"ts": 1}},
    ]

    docs = await collection.aggregate(pipeline).to_list(length=None)

    if not docs:
        return HistoricalDataResponse(
            user_id=payload.user_id,
            device_id=payload.device_id,
            device_name=payload.device_name,
            time_range_days=payload.time_range.value,
            bucket_minutes=bucket_minutes,
            total_points=0,
            data=[],
        )

    buckets: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for doc in docs:
        ts = doc.get("ts")
        if not isinstance(ts, datetime):
            continue
        bucket_start = _floor_to_bucket(ts, bucket_minutes)
        buckets[bucket_start].append(doc)

    points: list[HistoricalDataPoint] = []
    for bucket_start in sorted(buckets.keys()):
        bucket_docs = buckets[bucket_start]
        data_payload = _build_payload_from_bucket(bucket_docs, payload.device_name)
        points.append(
            HistoricalDataPoint(timestamp=_iso_utc(bucket_start), payload=data_payload)
        )

    return HistoricalDataResponse(
        user_id=payload.user_id,
        device_id=payload.device_id,
        device_name=payload.device_name,
        time_range_days=payload.time_range.value,
        bucket_minutes=bucket_minutes,
        total_points=len(points),
        data=points,
    )
