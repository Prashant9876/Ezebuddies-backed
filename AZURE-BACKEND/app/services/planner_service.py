from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.db.mongodb import get_client
from app.schemas.planner import (
    PlannerDeviceUpdateRequest,
    PlannerDeviceUpdateResponse,
    PlannerRequest,
    PlannerResponse,
    ResetManualLogRequest,
    ResetManualLogResponse,
    SinchaiPlannerResponse,
    UpdateSinchaiPlannerRequest,
    UpdateSinchaiPlannerResponse,
)
from app.services.mqtt_service import mqtt_publisher


def _candidate_collection_names(section: str) -> list[str]:
    names = [section, section.strip(), section.replace(" ", "_"), section.replace(" ", "")]
    unique_names: list[str] = []
    for name in names:
        if name and name not in unique_names:
            unique_names.append(name)
    return unique_names


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


def _nullify_zero_or_empty(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value == 0:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if isinstance(value, list):
        if len(value) == 0:
            return None
        return [_nullify_zero_or_empty(item) for item in value]
    if isinstance(value, dict):
        return {key: _nullify_zero_or_empty(val) for key, val in value.items()}
    return value


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


async def update_planner_device(
    payload: PlannerDeviceUpdateRequest, token_user_id: str
) -> PlannerDeviceUpdateResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update only your own planner data",
        )

    mongo_client = get_client()
    planner_collection = mongo_client[settings.login_db_name][settings.planner_collection_name]

    user_doc = await planner_collection.find_one({"user_id": payload.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planner data not found for this user",
        )

    existing_device: Optional[dict[str, Any]] = None
    for device in user_doc.get("devices", []):
        if str(device.get("device_id", "")).strip() == payload.device_id:
            existing_device = device
            break

    if not existing_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found in planner data",
        )

    sop_data: Optional[dict[str, Any]] = None
    if payload.crop_name:
        sop_collection = mongo_client[settings.sop_db_name][settings.sop_collection_name]
        sop_doc = await sop_collection.find_one(
            {"Crop_name": {"$regex": f"^{payload.crop_name}$", "$options": "i"}}
        )
        if not sop_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop SOP not found for provided crop_name",
            )
        sop_data = {
            key: _serialize_mongo_value(value)
            for key, value in sop_doc.items()
            if key != "_id"
        }

    update_fields: dict[str, Any] = {}
    if payload.crop_name is not None:
        update_fields["devices.$.crop_name"] = payload.crop_name
    if payload.sowing_date is not None:
        update_fields["devices.$.sowing_date"] = payload.sowing_date
    if payload.harvest_date is not None:
        update_fields["devices.$.harvest_date"] = payload.harvest_date

    update_result = await planner_collection.update_one(
        {"user_id": payload.user_id, "devices.device_id": payload.device_id},
        {"$set": update_fields},
    )
    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found for update",
        )

    updated_doc = await planner_collection.find_one({"user_id": payload.user_id})
    updated_device: Optional[dict[str, Any]] = None
    for device in updated_doc.get("devices", []):
        if str(device.get("device_id", "")).strip() == payload.device_id:
            updated_device = _serialize_mongo_value(device)
            break

    if not updated_device:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Device updated but could not be retrieved",
        )

    mqtt_topic: Optional[str] = None
    if sop_data is not None:
        mqtt_topic = f"farm/Sub/{payload.user_id}"
        mqtt_payload = {
            "CMD": "Updated_SOP",
            "user_id": payload.user_id,
            "device_id": payload.device_id,
            "crop_name": payload.crop_name,
            "sop_data": sop_data,
        }
        mqtt_publisher.publish(topic=mqtt_topic, payload=mqtt_payload)

    return PlannerDeviceUpdateResponse(
        message="Planner device updated successfully",
        user_id=payload.user_id,
        device_id=payload.device_id,
        updated_device=updated_device,
        sop_data=sop_data,
        mqtt_topic=mqtt_topic,
    )


async def get_sinchai_planner(
    token_type: str, user_id: str, section: str, token_user_id: str
) -> SinchaiPlannerResponse:
    if token_type.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="token_type must be bearer",
        )

    if token_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can access only your own sinchai planner data",
        )

    plan_doc = await _find_user_plan_doc(section=section, user_id=user_id)
    if not plan_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sinchai planner data not found for this user in requested section",
        )

    schedules = plan_doc.get("schedules", [])
    if not isinstance(schedules, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sinchai planner format is invalid: schedules is missing",
        )

    mode_value = plan_doc.get("mode", "")
    if not isinstance(mode_value, str):
        mode_value = str(mode_value)
    farm_id_value = plan_doc.get("farm_id", "")
    if not isinstance(farm_id_value, str):
        farm_id_value = str(farm_id_value)
    no_of_valves_value = plan_doc.get("No_of_valves", plan_doc.get("no_of_valves", 0))
    if not isinstance(no_of_valves_value, int):
        try:
            no_of_valves_value = int(no_of_valves_value)
        except Exception:
            no_of_valves_value = 0
    fertigation_time_min_value = plan_doc.get("fertigation_time_min", 0)
    if not isinstance(fertigation_time_min_value, int):
        try:
            fertigation_time_min_value = int(fertigation_time_min_value)
        except Exception:
            fertigation_time_min_value = 0
    manual_log_value = plan_doc.get("manual_log")
    if isinstance(manual_log_value, dict):
        manual_log_value = _serialize_mongo_value(manual_log_value)
    else:
        manual_log_value = None

    response_payload = {
        "user_id": user_id,
        "farm_id": farm_id_value,
        "section": section,
        "No_of_valves": no_of_valves_value,
        "fertigation_time_min": fertigation_time_min_value,
        "manual_log": manual_log_value,
        "mode": mode_value,
        "schedules": [_serialize_mongo_value(schedule) for schedule in schedules],
    }
    response_payload = _nullify_zero_or_empty(response_payload)

    return SinchaiPlannerResponse(
        user_id=response_payload["user_id"],
        farm_id=response_payload["farm_id"],
        section=response_payload["section"],
        No_of_valves=response_payload["No_of_valves"],
        fertigation_time_min=response_payload["fertigation_time_min"],
        manual_log=response_payload["manual_log"],
        mode=response_payload["mode"],
        schedules=response_payload["schedules"],
    )


async def update_sinchai_planner(
    payload: UpdateSinchaiPlannerRequest, token_user_id: str
) -> UpdateSinchaiPlannerResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can update only your own sinchai planner data",
        )

    section = "user_sinchai_planner"
    mongo_client = get_client()
    collection = mongo_client[settings.login_db_name][section]
    existing_doc = await collection.find_one({"user_id": payload.user_id})

    incoming_schedules = [
        _serialize_mongo_value(item.model_dump(exclude_none=True))
        for item in payload.schedules
    ]
    updated_count = 0
    added_count = 0

    if existing_doc:
        existing_schedules = existing_doc.get("schedules", [])
        if not isinstance(existing_schedules, list):
            existing_schedules = []

        existing_keys = {
            str(schedule.get("schedule_no", "")).strip()
            for schedule in existing_schedules
            if str(schedule.get("schedule_no", "")).strip()
        }
        incoming_keys = {
            str(schedule.get("schedule_no", "")).strip()
            for schedule in incoming_schedules
            if str(schedule.get("schedule_no", "")).strip()
        }
        updated_count = len(existing_keys.intersection(incoming_keys))
        added_count = len(incoming_keys - existing_keys)

        # Schedules are treated as a full replacement list:
        # if a schedule is omitted in payload, it is deleted from DB.
        merged_schedules = incoming_schedules

        update_fields: dict[str, Any] = {
            "mode": payload.mode,
            "schedules": merged_schedules,
            "updated_at": datetime.utcnow(),
        }
        if payload.No_of_valves is not None:
            update_fields["No_of_valves"] = payload.No_of_valves
        if payload.fertigation_time_min is not None:
            update_fields["fertigation_time_min"] = payload.fertigation_time_min

        await collection.update_one({"_id": existing_doc["_id"]}, {"$set": update_fields})
    else:
        added_count = len(incoming_schedules)
        doc_to_insert: dict[str, Any] = {
            "user_id": payload.user_id,
            "mode": payload.mode,
            "schedules": incoming_schedules,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        if payload.No_of_valves is not None:
            doc_to_insert["No_of_valves"] = payload.No_of_valves
        if payload.fertigation_time_min is not None:
            doc_to_insert["fertigation_time_min"] = payload.fertigation_time_min
        await collection.insert_one(doc_to_insert)

    latest_doc = await collection.find_one({"user_id": payload.user_id}) or {}
    mode_value = latest_doc.get("mode", payload.mode)
    if not isinstance(mode_value, str):
        mode_value = str(mode_value)
    no_of_valves_value = latest_doc.get("No_of_valves", 0)
    if not isinstance(no_of_valves_value, int):
        try:
            no_of_valves_value = int(no_of_valves_value)
        except Exception:
            no_of_valves_value = 0
    fertigation_time_min_value = latest_doc.get("fertigation_time_min", 0)
    if not isinstance(fertigation_time_min_value, int):
        try:
            fertigation_time_min_value = int(fertigation_time_min_value)
        except Exception:
            fertigation_time_min_value = 0

    schedules_value = latest_doc.get("schedules", [])
    if not isinstance(schedules_value, list):
        schedules_value = []

    return UpdateSinchaiPlannerResponse(
        message="Sinchai planner updated successfully",
        user_id=payload.user_id,
        section=section,
        mode=mode_value,
        No_of_valves=no_of_valves_value,
        fertigation_time_min=fertigation_time_min_value,
        schedules=[_serialize_mongo_value(schedule) for schedule in schedules_value],
        updated_count=updated_count,
        added_count=added_count,
    )


async def reset_manual_log(
    payload: ResetManualLogRequest, token_user_id: str
) -> ResetManualLogResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can reset manual log only for your own account",
        )

    section = "user_sinchai_planner"
    mongo_client = get_client()
    collection = mongo_client[settings.login_db_name][section]

    user_doc = await collection.find_one({"user_id": payload.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sinchai planner data not found for this user",
        )

    db_farm_id = user_doc.get("farm_id")
    if str(db_farm_id) != str(payload.farmid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm ID does not match for this user",
        )

    reset_value = {"timestamp": 0, "duration_min": 0, "valves": []}
    await collection.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"manual_log": reset_value, "updated_at": datetime.utcnow()}},
    )

    return ResetManualLogResponse(
        message="manual_log reset successfully",
        user_id=payload.user_id,
        farmid=str(payload.farmid),
        manual_log=reset_value,
    )
