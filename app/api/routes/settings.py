from app.apis import mongo
from time import perf_counter
from app.models import DResponse
from app.core.cron import fetch_metadata
from fastapi import Request, Response, APIRouter, BackgroundTasks


router = APIRouter(
    prefix="/settings",
    tags=["internals"],
)


@router.get("", response_model=dict, status_code=200)
def settings_get() -> dict:
    init_time = perf_counter()

    result = mongo.get_config()
    return DResponse(
        200, "Config successfully retrieved from database.", True, result, init_time
    ).__json__()


@router.post("", response_model=dict, status_code=200)
async def settings_post(
    request: Request, response: Response, background_tasks: BackgroundTasks
) -> dict:
    init_time = perf_counter()

    data = await request.json()
    condition = mongo.set_config(data)
    if condition == 0:
        response.status_code = 409
        return DResponse(
            409, "No changes were made to the config.", False, None, init_time
        ).__json__()
    elif condition == 1:
        return DResponse(
            200, "Config successfully uploaded to database.", True, None, init_time
        ).__json__()
    elif condition == 2:
        background_tasks.add_task(fetch_metadata)
        return DResponse(
            200,
            "Config successfully uploaded to database. Metadata generation started.",
            True,
            None,
            init_time,
        ).__json__()
