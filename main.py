import os
import time
import shlex
import uvicorn
from shutil import which
from sys import platform
from app import __version__
from io import TextIOWrapper
from asyncio.log import logger
from app.api import main_router
from app.settings import settings
from app.apis import mongo, rclone
from app.utils import time_formatter
from fastapi import FastAPI, Request
from app.core.rclone import RCloneAPI
from app.core.cron import fetch_metadata
from fastapi.staticfiles import StaticFiles
from apscheduler.triggers.cron import CronTrigger
from starlette.middleware.cors import CORSMiddleware
from subprocess import PIPE, STDOUT, DEVNULL, Popen, run
from fastapi.responses import FileResponse, UJSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from starlette.exceptions import HTTPException as StarletteHTTPException


if not settings.MONGODB_DOMAIN:
    logger.error("No MongoDB domain found! Exiting.")
    exit()
if not settings.MONGODB_USERNAME:
    logger.error("No MongoDB username found! Exiting.")
    exit()
if not settings.MONGODB_PASSWORD:
    logger.error("No MongoDB password found! Exiting.")
    exit()

start_time = time.time()


def restart_rclone():
    """Force closes any running instances of the Rclone port then starts an Rclone RC server"""
    if platform in ["win32", "cygwin", "msys"]:
        run(
            shlex.split(
                f"powershell.exe Stop-Process -Id (Get-NetTCPConnection -LocalPort {settings.RCLONE_LISTEN_PORT}).OwningProcess -Force"
            ),
            check=False,
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    elif platform in ["linux", "linux2"]:
        run(
            shlex.split(f"bash kill $(lsof -t -i:{settings.RCLONE_LISTEN_PORT})"),
            check=False,
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    elif platform in ["darwin"]:
        run(
            shlex.split(f"kill $(lsof -t -i:{settings.RCLONE_LISTEN_PORT})"),
            check=False,
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    else:
        exit("Unsupported platform")
    rclone_bin = which("rclone")
    rclone_process = Popen(
        shlex.split(
            f"{rclone_bin} rcd --rc-no-auth --rc-serve --rc-addr localhost:{settings.RCLONE_LISTEN_PORT} --config rclone.conf",
            posix=(platform not in ["win32", "cygwin", "msys"]),
        ),
        stdout=PIPE,
        stderr=STDOUT,
    )
    for line in TextIOWrapper(rclone_process.stdout, encoding="utf-8"):
        if "Serving remote control on" in line:
            time.sleep(1)
            break


def rclone_setup(categories: list):
    """Initializes the rclone.conf file"""
    rclone_conf = ""
    for item in mongo.config["rclone"]:
        rclone_conf += f"\n\n{item}"
    with open("rclone.conf", "w+", encoding="utf-8") as w:
        w.write(rclone_conf)

    restart_rclone()

    for i, category in enumerate(categories):
        rclone[i] = RCloneAPI(category, i)


def startup():
    """Initializes MongoDB and Rclone instances"""
    logger.info("Starting up...")

    logger.debug("Initializing core modules...")

    if mongo.get_is_config_init() is True:
        categories = mongo.get_categories()
        rclone_setup(categories)
        if mongo.get_is_metadata_init() is False:
            fetch_metadata()
        else:
            scheduler = BackgroundScheduler()
            trigger = CronTrigger.from_crontab(
                mongo.config["build"].get("cron", "0 */8 * * *")
            )
            scheduler.add_job(
                fetch_metadata, trigger, name="fetch_metadata", id="fetch_metadata"
            )
            scheduler.start()
        logger.debug("Done.")
    else:
        # logic for first time setup
        pass


app = FastAPI(title="Dester", openapi_url=f"{settings.API_V1_STR}/openapi.json")


@app.exception_handler(StarletteHTTPException)
async def static(request: Request, exception: StarletteHTTPException):
    """Returns the static build of the Frontend if available"""
    if exception.status_code == 404:
        if os.path.exists("build/index.html"):
            return FileResponse("build/index.html", media_type="text/html")
        else:
            return UJSONResponse(
                status_code=404, content={"ok": False, "message": "Are you lost?"}
            )
    elif exception.status_code == 500:
        return UJSONResponse(
            status_code=500, content={"ok": False, "message": "Internal server error"}
        )
    else:
        return UJSONResponse(
            status_code=exception.status_code,
            content={"ok": False, "message": "Unknown error"},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix=settings.API_V1_STR)
if os.path.exists("build/index.html"):
    app.mount("/", StaticFiles(directory="build/", html=True), name="static")
else:
    app.add_api_route(
        "/",
        lambda: {
            "ok": True,
            "message": "Backend is working.",
            "version": __version__,
            "uptime": time_formatter(time.time() - start_time),
        },
    )

startup()
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=False)
