from typing import Any, Dict
from time import perf_counter
from fastapi import Request, APIRouter


router = APIRouter(
    prefix="/settings",
    tags=["internals"],
)


@router.get("", response_model=Dict[str, Any], status_code=200)
def settings_get() -> Dict[str, Any]:
    start = perf_counter()
    from main import mongo

    config = mongo.get_config()
    return {
        "ok": True,
        "message": "success",
        "results": config,
        "time_taken": perf_counter() - start,
    }


@router.post("", response_model=Dict[str, Any], status_code=200)
async def settings_post(request: Request) -> Dict[str, Any]:
    start = perf_counter()
    from main import mongo

    data = await request.json()
    mongo.set_config(data)
    return {
        "ok": True,
        "message": "success",
        "time_taken": time.perf_counter() - start,
    }
