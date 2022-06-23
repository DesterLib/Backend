from app.apis import rclone
from httpx import AsyncClient
from time import perf_counter
from app.models import DResponse
from fastapi import Path, APIRouter
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


router = APIRouter(
    prefix="/assets",
    tags=["internals"],
)

client = AsyncClient()


@router.get("/image/{quality}/{filename}", status_code=200)
async def image_path(
    quality: str = Path(..., title="Quality for the requesting image"),
    filename: str = Path(..., title="Filename for the requesting image"),
):
    path = f"https://image.tmdb.org/t/p/{quality}/{filename}"
    req = client.build_request("GET", path)
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(), background=BackgroundTask(r.aclose), headers=r.headers
    )


@router.get(
    "/thumbnail/{rclone_index}/{file_id}",
    status_code=200,
)
async def image_path(
    file_id: str = Path(title := "File ID of the thumbnail that needs to be generated"),
    rclone_index: int = 0,
):
    init_time = perf_counter()

    thumb_url = rclone[rclone_index].thumbnail(file_id)
    if not thumb_url:
        return DResponse(
            404, "No thumbnail is available for this file.", False, None, init_time
        ).__json__()
    req = client.build_request("GET", thumb_url)
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(), background=BackgroundTask(r.aclose), headers=r.headers
    )
