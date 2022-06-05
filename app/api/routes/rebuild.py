from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks
from time import perf_counter
from app.core.cron import fetch_metadata

router = APIRouter(
    prefix="/rebuild",
    tags=["internals"],
)


@router.get("", response_model=Dict[str, Any], status_code=200)
async def rebuild(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    start = perf_counter()
    background_tasks.add_task(fetch_metadata)

    return {
        "ok": True,
        "message": "success",
        "time_taken": perf_counter() - start,
    }
