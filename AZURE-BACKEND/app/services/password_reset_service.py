import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import get_password_hash, hash_token
from app.db.mongodb import get_client
from app.schemas.password_reset import ForgotPasswordRequest, ForgotPasswordResponse


def _build_reset_email_html(reset_link: str, user_id: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#f6f9fc; padding:24px;">
        <div style="max-width:560px; margin:auto; background:white; border-radius:12px; padding:24px;">
          <h2 style="margin:0; color:#0b2545;">EZeBuddies Password Reset</h2>
          <p style="color:#334e68;">Hi {user_id},</p>
          <p style="color:#334e68;">
            We received a request to reset your password. Click the button below to continue.
            This reset link is valid for 15 minutes and can be used only once.
          </p>
          <p style="text-align:center; margin:24px 0;">
            <a href="{reset_link}" style="background:#0b8f6d; color:#fff; padding:12px 20px; border-radius:8px; text-decoration:none;">Reset Password</a>
          </p>
          <p style="color:#627d98; font-size:13px;">
            If you did not request this, please ignore this email.
          </p>
          <p style="color:#627d98; font-size:13px;">Team EZeBuddies</p>
        </div>
      </body>
    </html>
    """


def _send_reset_email(to_email: str, user_id: str, reset_link: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = "EZeBuddies - Reset Your Password"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email

    text_content = (
        f"Hi {user_id},\n\n"
        f"Use this link to reset your password (valid for 15 minutes, one-time use):\n"
        f"{reset_link}\n\n"
        "If you did not request this, ignore this email.\n"
        "Team EZeBuddies"
    )
    html_content = _build_reset_email_html(reset_link=reset_link, user_id=user_id)
    message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

    if settings.smtp_use_ssl:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
    try:
        if settings.smtp_use_tls and not settings.smtp_use_ssl:
            server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, [to_email], message.as_string())
    finally:
        server.quit()


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def request_password_reset(
    payload: ForgotPasswordRequest,
) -> ForgotPasswordResponse:
    mongo_client = get_client()
    users_collection = mongo_client[settings.login_db_name][settings.login_collection]
    reset_collection = mongo_client[settings.login_db_name][
        settings.reset_password_collection
    ]

    query: dict[str, Any] = {}
    if payload.user_id and payload.email:
        query = {"$or": [{"user_id": payload.user_id}, {"email": payload.email}]}
    elif payload.user_id:
        query = {"$or": [{"user_id": payload.user_id}, {"_id": payload.user_id}]}
    elif payload.email:
        query = {"email": payload.email}

    user_doc = await users_collection.find_one(query)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    resolved_user_id = str(user_doc.get("user_id") or user_doc.get("_id"))
    resolved_email = str(user_doc.get("email") or "")
    if not resolved_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email found for this user",
        )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.reset_token_expiry_minutes)

    await reset_collection.delete_many({"user_id": resolved_user_id})
    insert_result = await reset_collection.insert_one(
        {
            "user_id": resolved_user_id,
            "email": resolved_email,
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": expires_at,
        }
    )

    reset_link = (
        f"{settings.password_reset_base_url.rstrip('/')}/reset-password?token={raw_token}"
    )
    try:
        _send_reset_email(
            to_email=resolved_email, user_id=resolved_user_id, reset_link=reset_link
        )
    except Exception:
        await reset_collection.delete_one({"_id": insert_result.inserted_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send reset email",
        )

    return ForgotPasswordResponse(
        message="Reset password email sent",
        user_id=resolved_user_id,
        email=resolved_email,
    )


async def validate_reset_token(token: str) -> dict[str, Any]:
    mongo_client = get_client()
    reset_collection = mongo_client[settings.login_db_name][
        settings.reset_password_collection
    ]
    token_doc = await reset_collection.find_one({"token_hash": hash_token(token)})
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    expires_at = token_doc.get("expires_at")
    if not expires_at:
        await reset_collection.delete_one({"_id": token_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired",
        )

    if _to_utc(expires_at) < datetime.now(timezone.utc):
        await reset_collection.delete_one({"_id": token_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired",
        )
    return token_doc


async def reset_password_with_token(
    token: str, new_password: str, confirm_password: str
) -> None:
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match",
        )

    token_doc = await validate_reset_token(token)
    user_id = token_doc["user_id"]

    mongo_client = get_client()
    users_collection = mongo_client[settings.login_db_name][settings.login_collection]
    reset_collection = mongo_client[settings.login_db_name][
        settings.reset_password_collection
    ]

    password_hash = get_password_hash(new_password)
    result = await users_collection.update_one(
        {"$or": [{"user_id": user_id}, {"_id": user_id}]},
        {"$set": {"password_hash": password_hash, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for token",
        )

    await reset_collection.delete_one({"_id": token_doc["_id"]})
