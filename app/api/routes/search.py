from time import perf_counter
from enum import Enum
from fastapi import APIRouter
from typing import Any, Dict, Optional


router = APIRouter(
    prefix="/search",
    tags=["internals"],
)


class SortType(str, Enum):
    popularity = "popularity"
    rating = "rating"
    modified_time = "modified_time"
    release_date = "release_date"


unwanted_keys = [
    "cast",
    "seasons",
    "homepage",
    "file_name",
    "subtitles",
    "collection",
    "external_ids",
    "last_episode_to_air",
    "next_episode_to_air",
]


@router.get("", response_model=Dict[str, Any], status_code=200)
def query(
    query: Optional[str] = None,
    limit: Optional[int] = 10,
) -> Dict[str, Any]:
    start = perf_counter()
    from main import mongo

    unwanted_keys = {
        "_id": 0,
        "cast": 0,
        "seasons": 0,
        "file_name": 0,
        "subtitles": 0,
        "external_ids": 0,
        "collection": 0,
        "homepage": 0,
        "last_episode_to_air": 0,
        "next_episode_to_air": 0,
    }

    movies_match = []
    series_match = []
    for category in mongo.config["categories"]:
        result = mongo.metadata[category["id"]].aggregate(
            [
                {"$match": {"$text": {"$search": query}}},
                {"$sort": {"score": {"$meta": "textScore"}}},
                {"$limit": limit},
                {"$addFields": {"textScore": {"$meta": "textScore"}}},
                {"$project": unwanted_keys},
            ]
        )
        if category["type"] == "series":
            series_match.extend(result)
        else:
            movies_match.extend(result)
    results = {}
    results["movies"] = sorted(
        movies_match, key=lambda k: k["textScore"], reverse=True
    )[:limit]
    results["series"] = sorted(
        series_match, key=lambda k: k["textScore"], reverse=True
    )[:limit]
    return {
        "ok": True,
        "message": "success",
        "results": results,
        "time_taken": perf_counter() - start,
    }
