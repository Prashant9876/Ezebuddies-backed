from typing import Any

from pydantic import BaseModel, Field, model_validator


class SOPDataRequest(BaseModel):
    user_id: str = Field(min_length=1)
    crop_names: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_crop_names(self) -> "SOPDataRequest":
        cleaned = [name.strip() for name in self.crop_names if isinstance(name, str)]
        cleaned = [name for name in cleaned if name]
        if not cleaned:
            raise ValueError("crop_names must include at least one non-empty crop name")
        self.crop_names = cleaned
        return self


class SOPCropData(BaseModel):
    crop_name: str
    data: dict[str, Any]


class SOPDataResponse(BaseModel):
    user_id: str
    total_requested: int
    total_found: int
    found_crops: list[SOPCropData]
    missing_crops: list[str]

