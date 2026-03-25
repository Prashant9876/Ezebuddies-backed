from typing import Any

from pydantic import BaseModel, Field


class PlannerRequest(BaseModel):
    token_type: str = Field(default="bearer")
    user_id: str = Field(min_length=1)
    section: str = Field(min_length=1)


class PlannerResponse(BaseModel):
    user_id: str
    devices: list[dict[str, Any]]
