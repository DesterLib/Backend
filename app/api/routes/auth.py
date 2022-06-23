from fastapi import APIRouter
from app.apis import mongo


router = APIRouter(
    prefix="/auth",
    tags=["internals"],
)

@router.get("", response_model=dict, status_code=200)
def auth() -> dict:
    return mongo.config.get("auth0")
