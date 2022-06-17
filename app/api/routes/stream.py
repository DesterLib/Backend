import requests
from fastapi import Request, APIRouter
from fastapi.responses import StreamingResponse
from app.models import DResponse
from time import perf_counter
from datetime import datetime, timezone
from urllib.parse import parse_qs


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
        for chunk in stream.iter_content(chunk_size=4096):
            yield chunk


@router.get("/info/{rclone_index}/{id}", status_code=200)
def info(rclone_index: int, id: str):
    init_time = perf_counter()
    from main import rclone

    rc = rclone[rclone_index]
    qualities = {"37": "1080p HD", "22": "720p HD",
                 "59": "480p SD", "18": "360p SD"}
    if rc.fs_conf["token"]["expiry"] <= datetime.now():
        rc.refresh()
    transcoded_request = requests.get(
        "https://drive.google.com/get_video_info?docid=%s" % (id),
        headers={"Authorization": "Bearer %s" %
                 (rc.fs_conf["token"]["access_token"])},
    )
    transcoded_data = parse_qs(transcoded_request.text)
    streams = []
    if transcoded_data.get("status") == ["ok"]:
        for stream in transcoded_data["fmt_stream_map"]:
            split_stream = stream.split("|")
            streams.append(
                {"quality": qualities[split_stream[0]], "url": split_stream[1]})
    return DResponse(200, "A list of all available streams was successfully retrieved.", True, streams, init_time).__dict__()


@router.get("/{rclone_index}/{full_path:path}", status_code=206)
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

    return StreamingResponse(
        iter_file(result), headers=headers, status_code=result.status_code
    )
