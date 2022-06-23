import regex as re
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
    """Returns the newest log file in its entirety"""
    init_time = perf_counter()
    if path.exists("logs/dester.log"):
        with open("logs/dester.log", "r", encoding="utf-8") as r:
            result = r.read()
        return DResponse(
            200, "Most recent log file successfully retrieved.", True, result, init_time
        ).__json__()
    else:
        return DResponse(
            404, "The log file could not be found.", False, None, init_time
        ).__json__()


@router.get("/list", response_model=dict, status_code=200)
def list_logs() -> dict:
    """Returns a list of available logs"""
    init_time = perf_counter()
    result = [f for f in listdir("logs") if f.endswith(".log")]
    return DResponse(
        200, "List of log files successfully generated.", True, result, init_time
    ).__json__()


@router.get("/live", response_model=dict, status_code=200)
def live_logs() -> dict:
    """Returns a stream of live logs"""

    def stream(file: str):
        if path.exists(file):
            with open(file, "r", encoding="utf-8") as r:
                old_line = ""
                while True:
                    new_line = r.read()
                    if old_line != new_line:
                        result = ""
                        for line in new_line.splitlines()[-50:]:
                            match = re.search(r"(.*)\[(INFO|DEBUG|ERROR)\](.*)", line)
                            if match:
                                severity = match.group(2)
                                if severity == "INFO":
                                    style = "color: #30C42B;"
                                elif severity == "DEBUG":
                                    style = "color: #286CFF;"
                                elif severity == "ERROR":
                                    style = "color: #DB2662;"
                                line = f"<p><span style='{style}'>{match.group(1)}{severity}</span>{match.group(3)}</p>"
                                result += line
                                yield result
                            else:
                                line = f"<p>{line}</p>"
                                result += line
                                yield result
                        old_line = new_line
                        sleep(1)

    return StreamingResponse(stream("logs/dester.log"), media_type="text/plain")


@router.get("/{date}", response_model=dict, status_code=200)
def old_logs(date) -> dict:
    """Returns an older log file"""
    init_time = perf_counter()
    if path.exists(f"logs/dester{date}.log"):
        with open(f"logs/dester{date}.log", "r", encoding="utf-8") as r:
            result = r.read()
        return DResponse(
            200, "Most recent log file successfully retrieved.", True, result, init_time
        ).__json__()
    else:
        return DResponse(
            404, "The log file could not be found.", False, None, init_time
        ).__json__()
