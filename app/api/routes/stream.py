from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import requests


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


def iter_file(streamable):
    with streamable as stream:
        stream.raise_for_status()
        for chunk in stream.iter_content(chunk_size=16384):
            yield chunk


@router.get("/{rclone_index}/{full_path:path}")
def query(request: Request, full_path: str, rclone_index: int):
    from main import rclone

    rc = rclone[rclone_index]
    stream_url = rc.stream(full_path)

    result = requests.request(
        method=request.method,
        url=stream_url,
        headers=request.headers,
        allow_redirects=True,
        stream=True,
    )
    headers = result.headers
    headers["content-disposition"] = "inline"

    return StreamingResponse(iter_file(result), headers=headers, status_code=result.status_code)
