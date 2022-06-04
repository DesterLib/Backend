from time import time
from app import __version__
from typing import Any, Dict
from fastapi import APIRouter
from app.utils import time_formatter


router = APIRouter(
    prefix="/info",
    responses={404: {"message": "Are you lost?", "ok": False}},
    tags=["internals"],
)


@router.get("", response_model=Dict[str, Any], status_code=200)
def auth() -> Dict[str, Any]:
    from main import start_time

    return {
        "ok": True,
        "message": "Backend is working.",
        "version": __version__,
        "uptime": time_formatter(time() - start_time),
    }
