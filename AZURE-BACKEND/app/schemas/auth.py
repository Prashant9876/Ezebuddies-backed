from pydantic import AliasChoices, BaseModel, Field


class LoginRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("user_id", "id", "_id"),
        serialization_alias="user_id",
    )
    password: str = Field(min_length=1)


class DeviceResponse(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    is_active: bool
    deployed_at: str = ""


class SolutionResponse(BaseModel):
    solution_name: str
    devices: list[DeviceResponse]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    solutions: list[SolutionResponse]
