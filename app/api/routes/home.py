import time
from fastapi import APIRouter
from typing import Dict, Union


router = APIRouter(
    prefix="/home",
    tags=["internals"],
)

data_cap_limit = 15

unwanted_keys = {
    "_id": 0,
    "cast": 0,
    "crew": 0,
    "seasons": 0,
    "file_name": 0,
    "subtitles": 0,
    "external_ids": 0,
    "genres": 0,
    "videos": 0,
    "reviews": 0,
    "collection": 0,
    "homepage": 0,
    "last_episode_to_air": 0,
    "next_episode_to_air": 0,
    "path": 0,
    "parent": 0,
    "revenue": 0,
    "tagline": 0,
    "imdb_id": 0,
}


@router.get("", response_model=Dict[str, Union[str, int, float, bool, None, dict]])
def home() -> Dict[str, str]:
    start = time.perf_counter()
    from main import mongo

    if not mongo.is_config_init:
        return {
            "ok": False,
            "message": "The config needs to be initialized.",
            "redirect": "/settings",
        }

    most_popular_movies_data = list(mongo.movies_col.aggregate(
        [{"$sort": {"popularity": -1}}, {"$limit": data_cap_limit}, {"$project": unwanted_keys}]))
    most_popular_series_data = list(mongo.series_col.aggregate(
        [{"$sort": {"popularity": -1}}, {"$limit": data_cap_limit}, {"$project": unwanted_keys}]))
    carousel_data = []
    carousel_data.extend(
        most_popular_movies_data[:3] + most_popular_series_data[:3]
    )

    top_rated_movies_data = mongo.movies_col.aggregate(
        [
            {"$sort": {"rating": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )
    top_rated_series_data = mongo.series_col.aggregate(
        [
            {"$sort": {"rating": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )

    newly_released_movies_data = mongo.movies_col.aggregate(
        [
            {"$sort": {"modified_time": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )
    newly_released_episodes_data = mongo.series_col.aggregate(
        [
            {
                "$addFields": {
                    "last_episode_air_date": {
                        "$dateFromString": {
                            "dateString": "$last_episode_to_air.air_date"
                        }
                    }
                }
            },
            {"$sort": {"last_episode_air_date": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )

    newly_added_movies_data = mongo.movies_col.aggregate(
        [
            {"$sort": {"release_date": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )
    newly_added_episodes_data = mongo.series_col.aggregate(
        [
            {
                "$addFields": {
                    "last_episode_modified_time": {
                        "$first": {"$max": "$seasons.episodes.modified_time"}
                    }
                }
            },
            {"$sort": {"last_episode_modified_time": -1}},
            {"$limit": data_cap_limit},
            {"$project": unwanted_keys},
        ]
    )

    end = time.perf_counter()
    return {
        "ok": True,
        "message": "success",
        "data": {
            "carousel": carousel_data,
            "most_popular_movies": most_popular_movies_data,
            "most_popular_series": most_popular_series_data,
            "top_rated_movies": list(top_rated_movies_data),
            "top_rated_series": list(top_rated_series_data),
            "newly_released_movies": list(newly_released_movies_data),
            "newly_released_episodes": list(newly_released_episodes_data),
            "newly_added_movies": list(newly_added_movies_data),
            "newly_added_episodes": list(newly_added_episodes_data),
        },
        "time_taken": end - start,
    }
