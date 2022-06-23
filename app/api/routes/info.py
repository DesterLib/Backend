from time import time
from app import __version__
from fastapi import APIRouter
from app.utils import time_formatter


router = APIRouter(
    prefix="/info",
    tags=["internals"],
)


@router.get("", response_model=dict, status_code=200)
def auth() -> dict:
    from app.apis import start_time

    return {
        "message": "Backend is working.",
        "ok": True,
        "uptime": time_formatter(time() - start_time),
        "version": __version__,
    }
