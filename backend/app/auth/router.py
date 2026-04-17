from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import Config

from app.auth.dependencies import get_current_user
from app.auth.google_oauth import oauth
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    redirect_uri = str(request.url_for("auth_callback"))
    # Force HTTPS for the callback URL on Render (behind reverse proxy)
    redirect_uri = redirect_uri.replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri, hd=settings.allowed_domain)


@router.get("/callback", name="auth_callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    # Verify domain
    email = userinfo.get("email", "")
    hd = userinfo.get("hd", "")
    if hd != settings.allowed_domain:
        raise HTTPException(status_code=403, detail="Access denied. Only @haikugames.com accounts are allowed.")

    # Upsert user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        user.display_name = userinfo.get("name", email)
        user.avatar_url = userinfo.get("picture")
        user.last_login_at = datetime.now(timezone.utc)
    else:
        user = User(
            email=email,
            display_name=userinfo.get("name", email),
            avatar_url=userinfo.get("picture"),
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create JWT
    token_data = {"user_id": str(user.id), "email": user.email}
    session_token = jwt.encode(token_data, settings.session_secret_key, algorithm="HS256")

    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )
    return response


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout():
    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    response.delete_cookie("session")
    return response
