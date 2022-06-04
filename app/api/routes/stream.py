from fastapi import APIRouter, Request, Header
from typing import Any, Dict, Optional
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/stream",
    tags=["internals"],
)

@router.get("/{full_path:path}", status_code=206)
def query(request: Request, full_path: str, range: str = Header(None)) -> StreamingResponse:
    from main import rclone
    rc = rclone["1LwKkllwdyGeuETh3WTitreTSSEi3Nfyq"]
    req_headers = request.headers.items()
    start, end = range.replace("bytes=", "").split("-")
    result = rc.stream(full_path, req_headers)
    res_headers = {
        'Content-Range': f'bytes {start}-{end}',
        'Accept-Ranges': 'bytes'
    }
    print(result)
    return StreamingResponse(result.encode())
