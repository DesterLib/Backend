from os import getenv
from dotenv import load_dotenv
from pydantic import BaseSettings


load_dotenv()


class _Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    ON_HEROKU: bool = getenv("DYNO") is not None
    PORT: int = int(getenv("PORT", "35500"))
    DEVELOPMENT: bool = getenv("DESTER_DEV", "").lower() == "true"

    RCLONE_LISTEN_PORT: int = int(getenv("RCLONE_LISTEN_PORT", "35530"))

    MONGODB_DOMAIN: str = getenv("MONGODB_DOMAIN")
    MONGODB_USERNAME: str = getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD: str = getenv("MONGODB_PASSWORD")


settings = _Settings()
