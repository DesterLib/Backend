from fastapi import APIRouter
from httpx import AsyncClient


router = APIRouter(
    prefix="/auth",
    tags=["internals"],
)

client = AsyncClient()


@router.get("", response_model=dict, status_code=200)
def auth() -> dict:
    from main import mongo

    return mongo.config.get("auth0")
