from os import getenv
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class _Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    TMDB_API_KEY: Optional[str] = getenv("TMDB_API_KEY")
    CORS_ORIGINS = [
        "http://localhost",
        "http://localhost:35510",
    ]
    ON_HEROKU: bool = getenv("DYNO") is not None
    PORT: int = int(getenv("PORT", "35500"))
    DEVELOPMENT: bool = getenv("DESTER_DEV", "").lower() == "true"
    GDRIVE_CLIENT_ID: Optional[str] = getenv("GDRIVE_CLIENT_ID")
    GDRIVE_CLIENT_SECRET: Optional[str] = getenv("GDRIVE_CLIENT_SECRET")
    GDRIVE_ACCESS_TOKEN: Optional[str] = getenv("GDRIVE_ACCESS_TOKEN")
    GDRIVE_REFRESH_TOKEN: Optional[str] = getenv("GDRIVE_REFRESH_TOKEN")
    GDRIVE_SERVICE_ACCOUNT_JSON: Optional[str] = getenv("GDRIVE_SERVICE_ACCOUNT_JSON")

    AUTH0_GLOBAL_CLIENT_ID: str = getenv("AUTH0_GLOBAL_CLIENT_ID")
    AUTH0_GLOBAL_CLIENT_SECRET: str = getenv("AUTH0_GLOBAL_CLIENT_SECRET")
    AUTH0_DOMAIN: str = getenv("AUTH0_DOMAIN")
    LOGO_URL: str = getenv("LOGO_URL")


settings = _Settings()
