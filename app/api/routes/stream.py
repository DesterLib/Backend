from io import BytesIO, StringIO
from fastapi import Request, APIRouter
from fastapi.responses import StreamingResponse, Response


router = APIRouter(
    prefix="/stream",
    tags=["internals"],
)

excluded_headers = [
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "host",
]

@router.get("/{full_path:path}")
def query(request: Request, full_path: str):
    from main import rclone
    rc = rclone["1LwKkllwdyGeuETh3WTitreTSSEi3Nfyq"]

    req_headers = request.headers.items()
    res_headers = {"cache-control": "no-cache, no-store, must-revalidate", "pragma": "no-cache"}
    for item in req_headers:
        if item[0].lower() not in excluded_headers:
            res_headers[item[0]] = item[1]
    req_range = res_headers.get("Range") or res_headers.get("range") or ""
    result = rc.stream(full_path, req_range)

    return Response(result, media_type="video/mp4", headers=res_headers)
