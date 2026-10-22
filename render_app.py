import base64
import binascii
import os
import secrets

from starlette.responses import JSONResponse
from app.main import app as backend

USERNAME = os.environ.get("DEMO_USERNAME", "")
PASSWORD = os.environ.get("DEMO_PASSWORD", "")

if not USERNAME or len(PASSWORD) < 20:
    raise RuntimeError(
        "Set DEMO_USERNAME and DEMO_PASSWORD (at least 20 characters)."
    )


async def protected_app(scope, receive, send):
    if scope["type"] != "http":
        await backend(scope, receive, send)
        return

    if scope["path"] == "/health":
        await backend(scope, receive, send)
        return

    headers = dict(scope.get("headers", []))
    authorized = False

    try:
        scheme, token = headers.get(
            b"authorization", b""
        ).decode("ascii").split(" ", 1)

        if scheme.lower() == "basic":
            decoded = base64.b64decode(
                token, validate=True
            ).decode("utf-8")
            username, password = decoded.split(":", 1)

            user_ok = secrets.compare_digest(
                username.encode(), USERNAME.encode()
            )
            password_ok = secrets.compare_digest(
                password.encode(), PASSWORD.encode()
            )
            authorized = user_ok and password_ok
    except (ValueError, UnicodeError, binascii.Error):
        pass

    if not authorized:
        response = JSONResponse(
            {"detail": "Authentication required"},
            status_code=401,
            headers={
                "WWW-Authenticate": 'Basic realm="PrivacyVault demo"',
                "Cache-Control": "no-store",
            },
        )
        await response(scope, receive, send)
        return

    await backend(scope, receive, send)


from starlette.middleware.cors import CORSMiddleware
from app.config import settings

app = CORSMiddleware(
    protected_app,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
