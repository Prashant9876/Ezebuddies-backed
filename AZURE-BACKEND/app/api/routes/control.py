from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import get_current_user_id
from app.schemas.control import (
    ChangeRelayStateRequest,
    EStopRequest,
    MqttPublishResponse,
)
from app.services.mqtt_service import mqtt_publisher


router = APIRouter(tags=["Control"])


@router.post("/change_relay_state", response_model=MqttPublishResponse)
async def change_relay_state(
    payload: ChangeRelayStateRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> MqttPublishResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can control only your own devices",
        )

    topic = f"farm/Sub/{payload.user_id}"
    mqtt_payload = {
        "CMD": "Act_State_Update",
        "user_id": payload.user_id,
        "device_id": payload.device_id,
        "button_name": payload.button_name,
        "state": payload.state,
    }
    mqtt_publisher.publish(topic=topic, payload=mqtt_payload)

    return MqttPublishResponse(
        message="Relay state update published",
        topic=topic,
        payload=mqtt_payload,
    )


@router.post("/Estop", response_model=MqttPublishResponse)
async def estop(
    payload: EStopRequest,
    token_user_id: str = Depends(get_current_user_id),
) -> MqttPublishResponse:
    if token_user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can trigger E-Stop only for your own account",
        )

    topic = f"farm/Sub/{payload.user_id}"
    mqtt_payload = {
        "CMD": "E_Stop",
        "user_id": payload.user_id,
        "solution_name": payload.solution_name,
    }
    mqtt_publisher.publish(topic=topic, payload=mqtt_payload)

    return MqttPublishResponse(
        message="E-Stop command published",
        topic=topic,
        payload=mqtt_payload,
    )
