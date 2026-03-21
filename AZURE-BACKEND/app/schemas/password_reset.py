from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class ForgotPasswordRequest(BaseModel):
    user_id: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "ForgotPasswordRequest":
        if not self.user_id and not self.email:
            raise ValueError("Provide at least one field: user_id or email")
        return self


class ForgotPasswordResponse(BaseModel):
    message: str
    user_id: str
    email: EmailStr


class ResetPasswordFormRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)
