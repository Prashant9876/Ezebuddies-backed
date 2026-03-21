from typing import Any

from pydantic import BaseModel, Field


class UserDevicesDataResponse(BaseModel):
    user_id: str
    source_database: str
    source_collection: str
    total_records: int
    records: list[dict[str, Any]] = Field(default_factory=list)
