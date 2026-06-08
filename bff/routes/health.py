import os

import httpx
from fastapi import APIRouter

router = APIRouter()

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")


@router.get("/api/health")
async def health() -> dict[str, object]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ORCHESTRATOR_URL}/health", timeout=2.0)
        orchestrator_ok = resp.status_code == 200
    except httpx.HTTPError:
        orchestrator_ok = False
    return {"status": "ok", "orchestrator": orchestrator_ok}
