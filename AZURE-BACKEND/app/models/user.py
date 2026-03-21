from typing import Any
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Device(BaseModel):
    device_id: str
    device_name: str
    device_type: str = ""
    is_active: bool = True
    deployed_at: str = ""


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    name: str
    email: str
    password_hash: str
    devices: list[Device] = Field(default_factory=list)

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> "User":
        return cls.model_validate(data)
