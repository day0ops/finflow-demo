import os

from auth import get_user
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter()

_KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "")  # e.g. https://keycloak.example.com/realms/finflow
_APP_URL = os.getenv("APP_URL", "http://localhost:3000")


class MeResponse(BaseModel):
    username: str
    display_name: str
    role: str


@router.get("/api/me", response_model=MeResponse)
def get_me(request: Request) -> MeResponse:
    user = get_user(request)
    return MeResponse(username=user.username, display_name=user.display_name, role=user.role)


@router.get("/api/logout")
def logout():
    if _KEYCLOAK_ISSUER:
        end_session = f"{_KEYCLOAK_ISSUER}/protocol/openid-connect/logout?redirect_uri={_APP_URL}"
        return RedirectResponse(url=end_session, status_code=302)
    # Local dev: no Keycloak — redirect home (effectively a no-op)
    return RedirectResponse(url="/", status_code=302)
