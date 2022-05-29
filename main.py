import os
import time
import shlex
import uvicorn
from sys import platform
from app import __version__
from fastapi import FastAPI
from asyncio.log import logger
from app.api import main_router
from app.settings import settings
from app.utils import time_formatter
from app.core.cron import fetch_metadata
from fastapi.responses import UJSONResponse
from subprocess import STDOUT, DEVNULL, Popen, run
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core import TMDB, Metadata, RCloneAPI, LocalJsonDatabase, build_config


start_time = time.time()
config = LocalJsonDatabase(file_path="config.json")
metadata = Metadata(file_path="metadata.json")
rclone = {}


def startup():
    logger.info("Starting up...")
    if not config.get_from_col("auth0", "domain"):
        config.add_to_col("auth0", {"domain": settings.AUTH0_DOMAIN})
    if not config.get_from_col("auth0", "client_id"):
        config.add_to_col("auth0", {"client_id": settings.AUTH0_CLIENT_ID})
    if not config.get_from_col("auth0", "client_secret"):
        config.add_to_col("auth0", {"client_secret": settings.AUTH0_CLIENT_SECRET})

    if not config.get_from_col("rclone", "listen_port"):
        config.add_to_col("rclone", {"listen_port": settings.RCLONE_LISTEN_PORT})

    if not config.get("mongodb_uri"):
        config.set("mongodb_uri", settings.MONGODB_URI)

    if not config.get("categories"):
        config.set("categories", None)
    if not config.get("tmdb_api_key"):
        config.set("tmdb_api_key", settings.TMDB_API_KEY)
    rclone_conf = build_config(config)
    rclone_port = config.get_from_col("rclone", "listen_port")
    with open("rclone.conf", "w+") as w:
        w.write(rclone_conf)
    if platform in ["win32", "cygwin", "msys"]:
        run(
            shlex.split(
                f"powershell.exe Stop-Process -Id (Get-NetTCPConnection -LocalPort {rclone_port}).OwningProcess -Force"
            ),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    elif platform in ["linux", "linux2"]:
        run(
            shlex.split(f"bash kill $(lsof -t -i:{rclone_port})"),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    elif platform in ["darwin"]:
        run(
            shlex.split(f"kill $(lsof -t -i:{rclone_port})"),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
    else:
        exit("Unsupported platform")
    from shutil import which

    rclone_bin = which("rclone")
    rclone_bin_name = (
        "rclone.exe" if platform in ["win32", "cygwin", "msys"] else "rclone"
    )
    if not rclone_bin:
        if os.path.exists(f"bin/{rclone_bin_name}"):
            rclone_bin = f"bin/{rclone_bin_name}"
        else:
            from scripts.install_rclone import download_rclone

            rclone_bin = download_rclone()
    Popen(
        shlex.split(
            f"{rclone_bin} rcd --rc-no-auth --rc-addr localhost:{rclone_port} --config rclone.conf"
        )
    )

    categories = config.get("categories")
    for category in categories:
        id = category.get("id") or category.get("drive_id")
        provider = category.get("provider") or "gdrive"
        rclone[id] = RCloneAPI(id, provider)

    tmdb_api_key = config.get("tmdb_api_key")

    tmdb = TMDB(api_key=tmdb_api_key)
    logger.debug("Initializing core modules...")
    if not len(metadata):
        logger.debug("Metadata file is empty. Fetching metadata...")
        metadata.data = fetch_metadata(tmdb, categories)
        metadata.save()
        time.sleep(2)
    else:
        logger.debug("Metadata file is not empty. Skipping fetching metadata...")
    logger.debug("Done.")


app = FastAPI(
    title="DesterLib",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    exception_handlers={
        StarletteHTTPException: lambda req, exc: UJSONResponse(
            status_code=404, content={"ok": False, "message": "Are you lost?"}
        ),
        500: lambda req, exc: UJSONResponse(
            status_code=500,
            content={
                "ok": False,
                "message": "Internal server error",
                "error_msg": str(exc),
            },
        ),
    },
)

# Set all CORS enabled origins

if settings.DEVELOPMENT is True:
    allow_origins = ["*"]
else:
    allow_origins = [str(origin) for origin in settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix=settings.API_V1_STR)
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
    uvicorn.run("main:app", host="localhost", port=settings.PORT, reload=True)
