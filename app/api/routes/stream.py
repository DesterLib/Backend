import requests
from app.apis import rclone
from httpx import AsyncClient
from time import perf_counter
from app.models import DResponse
from urllib.parse import parse_qs
from fastapi import Request, APIRouter
from fastapi.responses import StreamingResponse


stream_client = AsyncClient()
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


@router.get("/info/{rclone_index}/{id}", status_code=200)
def info(rclone_index: int, id: str):
    init_time = perf_counter()

    rc = rclone[rclone_index]
    qualities = {"37": "1080p HD", "22": "720p HD", "59": "480p SD", "18": "360p SD"}
    transcoded_request = requests.get(
        "https://drive.google.com/get_video_info?docid=%s" % (id),
        headers={"Authorization": "Bearer %s" % (rc.fs_conf["token"]["access_token"])},
    )
    transcoded_data = parse_qs(transcoded_request.text)
    streams = []
    if transcoded_data.get("status") == ["ok"]:
        for stream in transcoded_data["fmt_stream_map"]:
            split_stream = stream.split("|")
            streams.append(
                {"quality": qualities[split_stream[0]], "url": split_stream[1]}
            )
    return DResponse(
        200,
        "A list of all available streams was successfully retrieved.",
        True,
        streams,
        init_time,
    ).__json__()


@router.get("/{rclone_index}/{full_path:path}", status_code=206)
async def stream_route(request: Request, full_path: str, rclone_index: int):
    rc = rclone[rclone_index]
    stream_url = rc.stream(full_path)
    req = stream_client.build_request("GET", stream_url, headers=request.headers.raw)
    resp = await stream_client.send(req, stream=True)
    headers = resp.headers
    headers["content-disposition"] = "inline"
    return StreamingResponse(
        resp.aiter_raw(), headers=headers, status_code=resp.status_code
    )
