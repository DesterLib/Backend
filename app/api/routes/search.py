from fastapi import APIRouter
from time import perf_counter
from typing import Any, Dict, Optional


router = APIRouter(
    prefix="/search",
    tags=["internals"],
)

unwanted_keys = {
    "_id": 0,
    "cast": 0,
    "crew": 0,
    "seasons": 0,
    "file_name": 0,
    "subtitles": 0,
    "external_ids": 0,
    "videos": 0,
    "reviews": 0,
    "collection": 0,
    "homepage": 0,
    "last_episode_to_air": 0,
    "next_episode_to_air": 0,
    "path": 0,
    "parent": 0,
    "description": 0,
    "revenue": 0,
    "tagline": 0,
    "imdb_id": 0,
    "genres": 0,
}


@router.get("", response_model=Dict[str, Any], status_code=200)
def query(
    query: Optional[str] = None,
    limit: Optional[int] = 10,
) -> Dict[str, Any]:
    start = perf_counter()
    from main import mongo

    movies_match = mongo.movies_col.aggregate(
        [
            {"$match": {"$text": {"$search": query}}},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": limit},
            {"$addFields": {"textScore": {"$meta": "textScore"}}},
            {"$project": unwanted_keys},
        ]
    )
    series_match = mongo.series_col.aggregate(
        [
            {"$match": {"$text": {"$search": query}}},
            {"$sort": {"score": {"$meta": "textScore"}}},
            {"$limit": limit},
            {"$addFields": {"textScore": {"$meta": "textScore"}}},
            {"$project": unwanted_keys},
        ]
    )
    results = {"movies": list(movies_match), "series": list(series_match)}
    return {
        "ok": True,
        "message": "success",
        "results": results,
        "time_taken": perf_counter() - start,
    }
