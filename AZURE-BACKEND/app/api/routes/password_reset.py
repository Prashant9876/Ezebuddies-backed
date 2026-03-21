from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.schemas.password_reset import ForgotPasswordRequest, ForgotPasswordResponse
from app.services.password_reset_service import (
    request_password_reset,
    reset_password_with_token,
    validate_reset_token,
)


router = APIRouter(tags=["Password Reset"])


def _reset_form_html(token: str, error: str = "") -> str:
    error_html = (
        f'<p style="color:#b42318; margin-bottom:16px;">{error}</p>' if error else ""
    )
    return f"""
    <html>
      <head><title>EZeBuddies - Reset Password</title></head>
      <body style="font-family: Arial, sans-serif; background: #f6f9fc; padding: 24px;">
        <div style="max-width: 460px; margin: auto; background: #fff; padding: 24px; border-radius: 12px;">
          <h2 style="margin-top:0; color:#0b2545;">Reset Password</h2>
          <p style="color:#334e68;">Set a new password for your EZeBuddies account.</p>
          {error_html}
          <form method="post" action="/reset-password">
            <input type="hidden" name="token" value="{token}" />
            <label>New Password</label><br/>
            <input type="password" name="new_password" required minlength="6" style="width:100%; padding:10px; margin:6px 0 14px;"/><br/>
            <label>Confirm Password</label><br/>
            <input type="password" name="confirm_password" required minlength="6" style="width:100%; padding:10px; margin:6px 0 18px;"/><br/>
            <button type="submit" style="background:#0b8f6d; color:#fff; border:none; padding:10px 16px; border-radius:8px;">Reset Password</button>
          </form>
          <p style="margin-top:18px; color:#627d98; font-size:13px;">EZeBuddies Support: contact@ezebuddies.com</p>
        </div>
      </body>
    </html>
    """


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    return await request_password_reset(payload)


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(token: str = Query(..., min_length=1)) -> HTMLResponse:
    try:
        await validate_reset_token(token)
    except HTTPException as exc:
        return HTMLResponse(
            content=_reset_form_html(token=token, error=exc.detail),
            status_code=400,
        )
    return HTMLResponse(content=_reset_form_html(token=token))


@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(
    token: str = Form(...),
    new_password: str = Form(..., min_length=6),
    confirm_password: str = Form(..., min_length=6),
) -> HTMLResponse:
    try:
        await reset_password_with_token(
            token=token, new_password=new_password, confirm_password=confirm_password
        )
    except HTTPException as exc:
        return HTMLResponse(
            content=_reset_form_html(token=token, error=exc.detail),
            status_code=400,
        )

    return HTMLResponse(
        content="""
        <html>
          <body style="font-family: Arial, sans-serif; background:#f6f9fc; padding:24px;">
            <div style="max-width:460px; margin:auto; background:#fff; border-radius:12px; padding:24px;">
              <h2 style="color:#0b2545; margin-top:0;">Password Updated</h2>
              <p style="color:#334e68;">Your password has been reset successfully. You can now log in with the new password.</p>
              <p style="color:#627d98; font-size:13px;">Team EZeBuddies</p>
            </div>
          </body>
        </html>
        """
    )
