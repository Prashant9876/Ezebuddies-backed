from pydantic import BaseModel, Field


class ChangeRelayStateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    button_name: str = Field(min_length=1)
    state: str = Field(min_length=1)


class EStopRequest(BaseModel):
    user_id: str = Field(min_length=1)
    solution_name: str = Field(min_length=1)


class MqttPublishResponse(BaseModel):
    success: bool = True
    message: str
    topic: str
    payload: dict
