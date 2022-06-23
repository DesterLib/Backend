import requests
from app.apis import mongo
from time import perf_counter
from app.models import DResponse
from fastapi import Response, APIRouter


router = APIRouter(
    prefix="/movie",
    tags=["internals"],
)


@router.get("/{id}", response_model=dict, status_code=200)
def movie(response: Response, id: int) -> dict:
    init_time = perf_counter()

    results = list(mongo.movies_col.find({"tmdb_id": id}, {"_id": 0}))
    if len(results) > 0:
        result = results[0]
        os_api_key = mongo.config["subtitles"].get("api_key")
        if os_api_key:
            subs = (
                requests.get(
                    f"https://api.opensubtitles.com/api/v1/subtitles?tmdb_id={id}&order_by=votes",
                    headers={"Api-Key": os_api_key},
                )
                .json()
                .get("data", [])[:5]
            )
            result["subtitles"] = subs
        return DResponse(
            200,
            f"Successfully retrieved a match for the TMDB ID {id}.",
            True,
            result,
            init_time,
            result["title"],
        ).__json__()
    else:
        response.status_code = 404
        return DResponse(
            404,
            f"No movies matching the TMDB ID {id} were found.",
            False,
            None,
            init_time,
        ).__json__()
