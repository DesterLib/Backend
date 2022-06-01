import time
from enum import Enum
from fastapi import APIRouter
from typing import Any, Dict, Optional


router = APIRouter(
    prefix="/settings",
    tags=["internals"],
)


@router.get("", response_model=Dict[str, Any], status_code=200)
def settings() -> Dict[str, Any]:
    start = time.perf_counter()
    from main import mongo

    config = mongo.get_config()
    return {
        "ok": True,
        "message": "success",
        "results": config,
        "time_taken": time.perf_counter() - start,
    }
