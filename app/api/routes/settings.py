import time
from enum import Enum
from fastapi import APIRouter, Request
from typing import Any, Dict, Optional


router = APIRouter(
    prefix="/settings",
    tags=["internals"],
)


@router.get("", response_model=Dict[str, Any], status_code=200)
def settings_get() -> Dict[str, Any]:
    start = time.perf_counter()
    from main import mongo

    config = mongo.get_config()
    return {
        "ok": True,
        "message": "success",
        "results": config,
        "time_taken": time.perf_counter() - start,
    }


@router.post("", response_model=Dict[str, Any], status_code=200)
async def settings_post(request: Request) -> Dict[str, Any]:
    start = time.perf_counter()
    from main import mongo

    data = await request.json()
    print(data)
    mongo.set_config(data)
    return {
        "ok": True,
        "message": "success",
        "time_taken": time.perf_counter() - start,
    }
