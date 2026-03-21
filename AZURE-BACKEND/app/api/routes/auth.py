from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_user


router = APIRouter(tags=["Auth"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "device-login-api"}


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    return await login_user(payload)
