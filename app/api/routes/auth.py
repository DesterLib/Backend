from typing import Any, Dict

from fastapi import APIRouter
from httpx import AsyncClient

router = APIRouter(
    prefix="/auth",
    # dependencies=[Depends(get_token_header)],
    responses={404: {"message": "Are you lost?", "ok": False}},
    tags=["internals"],
)

client = AsyncClient()


@router.get("", response_model=Dict[str, Any], status_code=200)
def auth() -> Dict[str, Any]:
    from main import config

    return config.get("auth0")
