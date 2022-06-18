from time import perf_counter
from app.models import DResponse
from app.core.cron import fetch_metadata
from fastapi import APIRouter, BackgroundTasks


router = APIRouter(
    prefix="/rebuild",
    tags=["internals"],
)


@router.get("", response_model=dict, status_code=200)
async def rebuild(background_tasks: BackgroundTasks) -> dict:
    init_time = perf_counter()
    background_tasks.add_task(fetch_metadata)

    return DResponse(
        200, "Metadata building task started in background.", True, None, init_time
    ).__json__()
