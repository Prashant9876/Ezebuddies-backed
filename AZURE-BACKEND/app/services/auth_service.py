from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.mongodb import get_client
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse


async def login_user(payload: LoginRequest) -> LoginResponse:
    mongo_client = get_client()
    users_collection = mongo_client[settings.login_db_name][settings.login_collection]
    user_doc = await users_collection.find_one(
        {"$or": [{"user_id": payload.user_id}, {"_id": payload.user_id}]}
    )

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_id or password",
        )

    try:
        user = User.from_mongo(user_doc)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile data is invalid",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_id or password",
        )

    auth_user_id = user.user_id or user.id
    token = create_access_token(subject=auth_user_id)
    return LoginResponse(
        access_token=token,
        user_id=auth_user_id,
        name=user.name,
        email=user.email,
        devices=[device.model_dump() for device in user.devices],
    )
