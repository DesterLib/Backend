import uvicorn
import ujson as json
from sys import platform
from subprocess import Popen, run, STDOUT, DEVNULL, CREATE_NO_WINDOW
from fastapi import FastAPI
from app.api import main_router
from app.settings import settings
from app.core.cron import fetch_metadata
from fastapi.responses import JSONResponse
from app.core import TMDB, Database, DriveAPI, Metadata
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.data import sort_by_type


config = Database(file_path="config.json")
metadata = Metadata(file_path="metadata.json")
drive = DriveAPI.initialize_drive(config)

def startup():
    print("Starting up...")
    if not config.get("auth0_domain"):
        config.set("auth0_domain", settings.AUTH0_DOMAIN)
    if not config.get("auth0_global_client_id"):
        config.set("auth0_global_client_id", settings.AUTH0_GLOBAL_CLIENT_ID)
    if not config.get("auth0_global_client_secret"):
        config.set("auth0_global_client_secret", settings.AUTH0_GLOBAL_CLIENT_ID)

    if not config.get("categories"):
        config.set("categories", None)
    if not config.get("tmdb_api_key"):
        config.set("tmdb_api_key", settings.TMDB_API_KEY)

    if platform in ["win32", "cygwin", "msys"]:
        run(
            "powershell.exe Stop-Process -Id (Get-NetTCPConnection -LocalPort 5572).OwningProcess -Force",
            stdout=DEVNULL,
            stderr=STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
        Popen("scripts/rclone.exe rcd --rc-no-auth --rc-addr localhost:35530")
    elif platform in ["linux", "linux2"]:
        run(
            "bash kill $(lsof -t -i:8080)",
            stdout=DEVNULL,
            stderr=STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
        Popen("scripts/rclone rcd --rc-no-auth --rc-addr localhost:35530")

    fully_initialized = True

    categories = config.get("categories")
    tmdb_api_key = config.get("tmdb_api_key")

    if fully_initialized:
        tmdb = TMDB(api_key=tmdb_api_key)
        print("Initializing core modules...")
        if not len(metadata):
            print("Metadata file is empty. Fetching metadata...")
            metadata.data = fetch_metadata(tmdb, categories)
            metadata.save()
        else:
            print("Metadata file is not empty. Skipping fetching metadata...")
        print("Done.")
    else:
        print("Not fully initialized. Skipping core modules...")


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
    uvicorn.run("main:app", host="localhost", port=settings.PORT, reload=False)
