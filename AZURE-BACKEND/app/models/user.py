from typing import Any
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Device(BaseModel):
    device_id: str
    device_name: str
    device_type: str = ""
    is_active: bool = True
    deployed_at: str = ""


class Solution(BaseModel):
    solution_name: str
    devices: list[Device] = Field(default_factory=list)


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = Field(default="", validation_alias="Phone")
    farm_location: Optional[str] = Field(default="", validation_alias="Farm_location")
    password_hash: str
    solutions: list[Solution] = Field(default_factory=list)
    devices: list[Device] = Field(default_factory=list)

    @classmethod
    def from_mongo(cls, data: dict[str, Any]) -> "User":
        return cls.model_validate(data)

    def get_solutions(self) -> list[Solution]:
        if self.solutions:
            return self.solutions
        if self.devices:
            return [Solution(solution_name="Default", devices=self.devices)]
        return []

    def get_all_devices(self) -> list[Device]:
        if self.solutions:
            devices: list[Device] = []
            for solution in self.solutions:
                devices.extend(solution.devices)
            return devices
        return self.devices
