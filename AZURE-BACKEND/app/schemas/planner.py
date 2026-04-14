from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class PlannerRequest(BaseModel):
    token_type: str = Field(default="bearer")
    user_id: str = Field(min_length=1)
    section: str = Field(min_length=1)


class PlannerResponse(BaseModel):
    user_id: str
    devices: list[dict[str, Any]]


class PlannerDeviceUpdateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    crop_name: Optional[str] = None
    sowing_date: Optional[str] = None
    harvest_date: Optional[str] = None

    @model_validator(mode="after")
    def validate_at_least_one_update(self) -> "PlannerDeviceUpdateRequest":
        if not any([self.crop_name, self.sowing_date, self.harvest_date]):
            raise ValueError(
                "At least one field is required: crop_name, sowing_date, harvest_date"
            )
        return self


class PlannerDeviceUpdateResponse(BaseModel):
    message: str
    user_id: str
    device_id: str
    updated_device: dict[str, Any]
    sop_data: Optional[dict[str, Any]] = None
    mqtt_topic: Optional[str] = None


class SinchaiPlannerResponse(BaseModel):
    user_id: str
    farm_id: str
    section: str
    mode: str
    schedules: list[dict[str, Any]]
