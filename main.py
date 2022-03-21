import random
import uvicorn
import ujson as json
from fastapi import FastAPI
from app.api import main_router
from app.settings import settings
from app.core.cron import fetch_metadata
from fastapi.responses import JSONResponse
from app.core import TMDB, Database, DriveAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException



config = Database(file_path="config.json")
metadata = Database(file_path="metadata.json")
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
    
    fully_initialized = True
    
    categories = config.get("categories")
    tmdb_api_key = config.get("tmdb_api_key")

    if fully_initialized:

        tmdb = TMDB(api_key=tmdb_api_key)
        print("Initializing core modules...")
        if not len(metadata):
            print("Metadata file is empty. Fetching metadata...")
            data = fetch_metadata(drive, tmdb, config.get("categories"))
            json.dump(data, open(metadata.path, "w"), indent=2)
        else:
            print("Metadata file is not empty. Skipping fetching metadata...")
        print("Done.")
    else:
        print("Not fully initialized. Skipping core modules...")

app = FastAPI(
    title="DesterLib", openapi_url=f"{settings.API_V1_STR}/openapi.json",
    exception_handlers={StarletteHTTPException: lambda req, exc: JSONResponse(status_code=404, content={"message": "Are you lost?"}),
                        500: lambda req, exc: JSONResponse(status_code=500, content={"message": "Internal server error"})},
    
)

# Set all CORS enabled origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    startup()
    uvicorn.run("main:app", host="localhost", port=settings.PORT)