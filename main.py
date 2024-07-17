import os
from pathlib import Path
import re
import time
import shlex
import asyncio
import uvicorn
from shutil import which
from sys import platform
from fastapi import FastAPI
from app.api import main_router
from app.settings import settings
from app.apis import rclone
from app.utils import time_formatter
from fastapi.staticfiles import StaticFiles
from subprocess import PIPE, STDOUT, DEVNULL, run
from app import logger, __version__, db
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, UJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import psutil

START_TIME = time.time()



async def kill_rclone():
    for conn in psutil.net_connections():
        if conn.laddr.port == settings.rclone_port:
            try:
                process = psutil.Process(conn.pid)
                process.terminate()
                process.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass
            except psutil.TimeoutExpired:
                process.kill()

async def restart_rclone():
    """Force closes any running instances of the Rclone port then starts an Rclone RC server"""
    await kill_rclone()
    if not os.path.isdir("bin"):
        os.mkdir("bin")
    rclone_bin = (
        f"bin/rclone{'.exe' if platform in ('win32', 'cygwin', 'msys') else ''}"
    )
    if not os.path.exists(rclone_bin):
        rclone_bin = which("rclone")
    if not rclone_bin:
        from scripts.install_rclone import download_rclone

        rclone_bin = download_rclone()
        if not rclone_bin:
            logger.error("Couldn't find rclone executable")
            logger.error(
                "Please download a suitable executable of rclone from 'rclone.org' and move it to the 'bin' folder."
            )
            quit(1)
    try:
        rclone_process = await asyncio.create_subprocess_exec(
            *shlex.split(
                f"{rclone_bin} rcd --rc-no-auth --rc-serve --rc-addr localhost:{settings.rclone_port} --config rclone.conf --log-level INFO",
                posix=(platform not in ("win32", "cygwin", "msys")),
            ),
            stdout=PIPE,
            stderr=STDOUT,
        )
    except PermissionError:
        await (
            await asyncio.create_subprocess_exec("chmod", "+x", rclone_bin)
        ).communicate()
        rclone_process = await asyncio.create_subprocess_exec(
            *shlex.split(
                f"{rclone_bin} rcd --rc-no-auth --rc-serve --rc-addr localhost:{settings.rclone_port} --config rclone.conf --log-level INFO",
                posix=(platform not in ("win32", "cygwin", "msys")),
            ),
            stdout=PIPE,
            stderr=STDOUT,
        )
    while True:
        out_line = await rclone_process.stdout.readline()
        if out_line == b"" and rclone_process.returncode == 0:
            err = await rclone_process.stderr.readline()
            logger.error("Failed to start rclone subprocess")
            logger.error(err.decode())
            break
        if "Serving remote control on" in out_line.decode():
            await asyncio.sleep(1)
            break
    logger.info("Started rclone")
    asyncio.create_task(log_rclone(rclone_process))


async def log_rclone(rclone_process: asyncio.subprocess.Process):
    rclone_logger = logger.getChild("rclone")
    rclone_logger.info("Starting rclone logger")
    while True:
        try:
            out_line = await rclone_process.stdout.readline()
            if out_line == b"":
                if rclone_process.returncode == 1:
                    err = await rclone_process.stderr.readline()
                    logger.error("An error occurred with rclone subprocess")
                    logger.error(err.decode())
                    break
                elif rclone_process.returncode == 0:
                    logger.warning("Rclone subprocess has ended gracefully")
                    break
                else:
                    rclone_logger.error("parse error: empty line")
                    continue
            match = re.match(
                r"(?:[\d\/])+ (?:[\d:]+) (?P<level>\w+) ? ? :? (?P<message>.*)$",
                out_line.decode(),
                flags=2,
            )
            data = match.groupdict()
            levels = {
                "CRITICAL": 50,
                "FATAL": 50,
                "ERROR": 40,
                "WARNING": 30,
                "WARN": 30,
                "INFO": 20,
                "DEBUG": 10,
            }
            rclone_logger.log(
                levels.get(data.get("levels", "INFO").upper()), data.get("message")
            )
        except Exception as e:
            rclone_logger.error(e)
            break


# async def rclone_setup(categories: list):
async def rclone_setup():
    """Initializes the rclone.conf file"""
    rclone_conf = await db.get_config("rclone.conf")
    if not os.path.exists("rclone.conf"):
        logger.error("rclone.conf not found")
        if not rclone_conf:
            logger.error("rclone.conf not found in database")
            exit(1)
        rclone_conf_str = "\n\n".join(rclone_conf.split("\n"))
        logger.error("writing rclone.conf from database")
        with open("rclone.conf", "w+", encoding="utf-8") as w:
            w.write(rclone_conf_str)
    else:
        logger.warning("rclone.conf already exists")
        logger.info("Syncing rclone.conf with database")
        rclone_conf = open("rclone.conf", "r", encoding="utf-8").read()
        await db.set_config("rclone.conf", rclone_conf)
    await restart_rclone()
    # for i, category in enumerate(categories):
    #     rclone[i] = RCloneAPI(category, i)

# async def build_metadata():
#     while True:
#         trigger = mongo.get_next_build_time()
#         sleep_seconds = abs(datetime.now(tz=timezone.utc) - trigger).total_seconds()
#         logger.info("Next run on %s", trigger.strftime("%d/%m/%Y, %H:%M:%S"))
#         await asyncio.sleep(sleep_seconds)
#         fetch_metadata()


async def startup():
    """Initializes MongoDB and Rclone instances"""
    logger.info("Starting up...")

    logger.info("Initializing database...")
    await db.init()
    logger.debug("Initializing core modules...")
    await rclone_setup()
    # if mongo.get_is_config_init() is True:
    #     categories = mongo.get_categories()
    #     logger.debug("Done.")
    # else:
    #     logger.warning("The site's configuration is not set up")
        # logic for first time setup


app = FastAPI(
    title="Dester",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    on_startup=[startup],
)


@app.exception_handler(StarletteHTTPException)
async def static(_, exception: StarletteHTTPException):
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

app.include_router(main_router, prefix=settings.api_v1_str)
if os.path.exists("build/index.html"):
    app.mount("/", StaticFiles(directory="build/", html=True), name="static")
else:
    app.add_api_route(
        "/",
        lambda: {
            "ok": True,
            "message": "Backend is working.",
            "version": __version__,
            "uptime": time_formatter(time.time() - START_TIME),
        },
    )
    
    app.add_api_route(
        "/favicon.ico",
        lambda: FileResponse("favicon.ico", media_type="image/x-icon"),
    )

# import asyncio

# async def main():
#     await startup()
# asyncio.create_task(startup())
# loop.create_task(build_metadata())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=False)

