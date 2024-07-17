from app import db
from fastapi import APIRouter


router = APIRouter(
    prefix="/auth",
    tags=["internals"],
)


@router.get("", response_model=dict, status_code=200)
def auth() -> dict:
    return db.get_config("auth0")
