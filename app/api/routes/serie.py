from typing import Any, Dict
from fastapi import APIRouter
from time import perf_counter


router = APIRouter(
    prefix="/serie",
    tags=["internals"],
)


@router.get("/{id}", response_model=Dict[str, Any], status_code=200)
def serie(id: int) -> Dict[str, Any]:
    start = perf_counter()
    from main import mongo

    results = list(mongo.series_col.find({"tmdb_id": id}, {"_id": 0}))
    if len(results) > 0:
        result = results[0]
        return {
            "ok": True,
            "message": "success",
            "results": result,
            "time_taken": perf_counter() - start,
        }
    else:
        return {
            "ok": False,
            "message": "No matches found.",
            "time_taken": perf_counter() - start,
        }
