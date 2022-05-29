from typing import Any, Dict
from httpx import AsyncClient
from fastapi import Path, APIRouter
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


router = APIRouter(
    prefix="/assets",
    # dependencies=[Depends(get_token_header)],
    responses={404: {"message": "Are you lost?", "ok": False}},
    tags=["internals"],
)

client = AsyncClient()


@router.get(
    "/image/{quality}/{filename}", response_model=Dict[str, Any], status_code=200
)
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


@router.get("/thumbnail/{file_id}", response_model=Dict[str, Any], status_code=200)
async def image_path(
    file_id: str = Path(title := "File ID of the thumbnail that needs to be generated"),
):
    from main import rclone

    # need to add a way to identify the correct remote
    # for now, I'll be using index 0
    thumb_url = rclone[list(rclone.keys())[0]].thumbnail(file_id)
    if not thumb_url:
        return {"ok": False, "message": "Thumbnail not found"}
    req = client.build_request("GET", thumb_url)
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(), background=BackgroundTask(r.aclose), headers=r.headers
    )
