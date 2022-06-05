from io import BytesIO
from fastapi import Request, APIRouter
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/stream",
    tags=["internals"],
)


@router.get("/{full_path:path}", status_code=206)
def query(request: Request, full_path: str) -> StreamingResponse:
    from main import rclone

    rc = rclone["1LwKkllwdyGeuETh3WTitreTSSEi3Nfyq"]

    req_headers = request.headers.items()
    result = rc.stream(full_path, req_headers).encode()

    return StreamingResponse(BytesIO(result), media_type="video/mp4", status_code=206)
