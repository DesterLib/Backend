from typing import Any, Dict
from fastapi import APIRouter, Response
from time import perf_counter
from app.models import DResponse


router = APIRouter(
    prefix="/movie",
    tags=["internals"],
)


@router.get("/{id}", response_model=dict, status_code=200)
def movie(response: Response, id: int) -> dict:
    init_time = perf_counter()
    from main import mongo

    results = list(mongo.movies_col.find({"tmdb_id": id}, {"_id": 0}))
    if len(results) > 0:
        result = results[0]
        return DResponse(200, f"Successfully retrieved a match for the TMDB ID {id}.", True, result, init_time).__dict__()
    else:
        response.status_code = 404
        return DResponse(404, f"No movies matching the TMDB ID {id} were found.", False, None, init_time).__dict__()
