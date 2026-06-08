"""
auth.py — User identity extraction for the FinFlow BFF.

When AUTH_ENABLED=true (production / k8s):
  AgentGateway validates the Keycloak session and forwards the ID token as the
  `jwt` request header (configured via `headers.idTokenHeader: jwt` in the
  AuthConfig). The BFF decodes the payload to extract user identity — signature
  verification is intentionally skipped because AgentGateway already verified
  the token before forwarding it.

When AUTH_ENABLED=false (local dev, default):
  Returns a hardcoded default user so the BFF works without Keycloak running.
  DEFAULT_USER and DEFAULT_ROLE can be overridden via env vars.

JWT claims used:
  preferred_username  → UserContext.username (maps to holdings.user_id in DB)
  given_name          → part of display_name
  family_name         → part of display_name
  role                → UserContext.role (custom claim, set via Keycloak protocol mapper)
"""

import base64
import json
import os

from fastapi import Request

_AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
_DEFAULT_USER = os.getenv("DEFAULT_USER", "morgan")
_DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "trader")


class UserContext:
    def __init__(self, username: str, display_name: str, role: str):
        self.username = username
        self.display_name = display_name
        self.role = role


def _decode_jwt_payload(token: str) -> dict:
    """Base64-decode the JWT payload segment (no signature verification)."""
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


def get_user(request: Request) -> UserContext:
    if not _AUTH_ENABLED:
        name = _DEFAULT_USER.capitalize()
        return UserContext(username=_DEFAULT_USER, display_name=name, role=_DEFAULT_ROLE)

    raw = request.headers.get("jwt", "")
    if raw.lower().startswith("bearer "):
        raw = raw[7:]

    payload = _decode_jwt_payload(raw)
    username = payload.get("preferred_username", _DEFAULT_USER)
    given = payload.get("given_name", "")
    family = payload.get("family_name", "")
    display_name = f"{given} {family}".strip() or username.capitalize()
    role = payload.get("role", _DEFAULT_ROLE)

    return UserContext(username=username, display_name=display_name, role=role)
