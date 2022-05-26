import shlex
from subprocess import DEVNULL, STDOUT, Popen, run
from sys import platform

import ujson as json
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api import main_router
from app.core import TMDB, Database, Metadata, RCloneAPI
from app.core.cron import fetch_metadata
from app.settings import settings
from app.utils.data import sort_by_type

config = Database(file_path="config.json")
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

    if not config.get("categories"):
        config.set("categories", None)
    if not config.get("tmdb_api_key"):
        config.set("tmdb_api_key", settings.TMDB_API_KEY)

    rclone_conf = ""
    client_id = config.get_from_col("gdrive", "client_id")
    client_secret = config.get_from_col("gdrive", "client_secret")
    token = json.dumps(
        {
            "access_token": config.get_from_col("gdrive", "access_token"),
            "token_type": "Bearer",
            "refresh_token": config.get_from_col("gdrive", "refresh_token"),
            "expiry": "2022-03-27T00:00:00.000+00:00",
        },
        escape_forward_slashes=False,
    )
    for category in config.get("categories"):
        id = category["id"]
        drive_id = category["drive_id"]
        rclone_conf += f"[{id}]\ntype = drive\nclient_id = {client_id}\nclient_secret = {client_secret}\nscope = drive\nroot_folder_id = {id}\ntoken = {token}\nteam_drive = {drive_id}\n"
    with open("rclone.conf", "w+") as w:
        w.write(rclone_conf)
    if platform in ["win32", "cygwin", "msys"]:
        run(
            shlex.split(
                "powershell.exe Stop-Process -Id (Get-NetTCPConnection -LocalPort 35530).OwningProcess -Force"
            ),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
        Popen(
            shlex.split(
                "scripts/rclone.exe rcd --rc-no-auth --rc-addr localhost:35530 --config rclone.conf"
            )
        )
    elif platform in ["linux", "linux2"]:
        run(
            shlex.split("bash kill $(lsof -t -i:35530)"),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
        Popen(
            "scripts/rclone rcd --rc-no-auth --rc-addr localhost:35530 --config rclone.conf"
        )
    elif platform in ["darwin"]:
        run(
            shlex.split("kill $(lsof -t -i:35530)"),
            stdout=DEVNULL,
            stderr=STDOUT,
        )
        Popen(
            shlex.split(
                "scripts/rclone rcd --rc-no-auth --rc-addr localhost:35530 --config rclone.conf"
            )
        )

    categories = config.get("categories")
    for category in categories:
        rclone[id] = RCloneAPI(id)

    tmdb_api_key = config.get("tmdb_api_key")

    tmdb = TMDB(api_key=tmdb_api_key)
    logger.debug("Initializing core modules...")
    if not len(metadata):
        logger.debug("Metadata file is empty. Fetching metadata...")
        metadata.data = fetch_metadata(tmdb, categories)
        metadata.save()
    else:
        logger.debug("Metadata file is not empty. Skipping fetching metadata...")
    logger.debug("Done.")


app = FastAPI(
    title="DesterLib",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    exception_handlers={
        StarletteHTTPException: lambda req, exc: JSONResponse(
            status_code=404, content={"ok": False, "message": "Are you lost?"}
        ),
        500: lambda req, exc: JSONResponse(
            status_code=500, content={"ok": False, "message": "Internal server error"}
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

startup()
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=settings.PORT, reload=True)
