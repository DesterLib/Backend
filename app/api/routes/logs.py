from os import path, listdir
from fastapi import APIRouter
from app.models import DResponse
from time import sleep, perf_counter
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/logs",
    tags=["internals"],
)


@router.get("", response_model=dict, status_code=200)
def logs() -> dict:
    init_time = perf_counter()
    if path.exists("logs/dester.log"):
        with open("logs/dester.log", "r") as r:
            result = r.read()
        return DResponse(
            200, "Most recent log file successfully retrieved.", True, result, init_time
        ).__dict__()
    else:
        return DResponse(
            404, "The log file could not be found.", False, None, init_time
        ).__dict__()


@router.get("/list", response_model=dict, status_code=200)
def list_logs() -> dict:
    init_time = perf_counter()
    result = [f for f in listdir("logs") if f.endswith(".log")]
    return DResponse(
        200, "List of log files successfully generated.", True, result, init_time
    ).__dict__()


@router.get("/live", response_model=dict, status_code=200)
def live_logs() -> dict:
    def stream(file: str):
        with open(file, "r") as r:
            while True:
                yield r.read()
                sleep(1.5)

    return StreamingResponse(stream("logs/dester.log"), media_type="text/plain")


@router.get("/{date}", response_model=dict, status_code=200)
def old_logs(date) -> dict:
    init_time = perf_counter()
    if path.exists(f"logs/dester{date}.log"):
        with open(f"logs/dester{date}.log", "r") as r:
            result = r.read()
        return DResponse(
            200, "Most recent log file successfully retrieved.", True, result, init_time
        ).__dict__()
    else:
        return DResponse(
            404, "The log file could not be found.", False, None, init_time
        ).__dict__()
