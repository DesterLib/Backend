import requests
from fastapi import APIRouter
from time import perf_counter
from app.models import DResponse


router = APIRouter(
    prefix="/subtitle",
    tags=["internals"],
)


@router.get("/{id}", status_code=200)
def subtitle(id: int) -> dict:
    init_time = perf_counter()
    from main import mongo

    os_api_key = mongo.config["subtitles"].get("api_key")
    result = requests.post(
        "https://api.opensubtitles.com/api/v1/download",
        headers={"Api-Key": os_api_key},
        data={"file_id": id},
    ).json()

    return DResponse(
        200,
        f"Successfully retrieved subtitle information.",
        True,
        result,
        init_time,
    ).__json__()
