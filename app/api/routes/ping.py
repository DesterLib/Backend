from fastapi import APIRouter
from typing import Dict, Union


router = APIRouter(
    prefix="/ping",
    tags=["misc"],
)


@router.get("", response_model=Dict[str, Union[str, bool]])
def ping() -> Dict[str, str]:
    """
    Just pings the server.
    """
    return {"ok": True, "message": "pong"}
