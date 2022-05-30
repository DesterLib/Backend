import time
import random
from copy import deepcopy
from diskcache import Cache
from fastapi import APIRouter
from typing import Any, Dict, Union
from app import logger

router = APIRouter(
    # dependencies=[Depends(get_token_header)],
    prefix="/home",
    responses={404: {"description": "Not found"}},
    tags=["internals"],
)

data_cap_limit = 15

cache = Cache(directory="cache", timeout=60 * 10)
# This current implementation is not optimal since it just straight up deletes all the cache.
# Which forces the script to regenerate the cache causing delay to user-end.
# A better way is to run a cron job to update the cache every 'x' seconds and provide the data
# which reduces any delay, I haven't implemented it cuz I plan to use asyncio here but the code itself is not compatible with asyncio yet.


@router.get("", response_model=Dict[str, Union[str, int, float, bool, None, dict]])
def home() -> Dict[str, str]:
    start = time.perf_counter()
    data = cache.get("home_route_data")
    if not data:
        logger.debug("Generating new data for home route")
        from main import metadata

        random.seed(100)
        categories_data = []
        carousel_data = []
        top_rated_series_data = []
        top_rated_movies_data = []
        newly_added_movies_data = []
        newly_added_episodes_data = []
        unwanted_keys = [
            "cast",
            "seasons",
            "file_name",
            "subtitles",
            "external_ids",
            "collection",
            "homepage",
            "last_episode_to_air",
            "next_episode_to_air",
        ]
        for category in metadata.frozen_data:
            if category["include_in_homepage"]:
                sorted_data = sorted(
                    category["metadata"],
                    key=lambda k: k["popularity"],
                    reverse=True,
                )
                sorted_data = sorted_data[:data_cap_limit]
                for item in sorted_data:
                    [item.pop(key, None) for key in unwanted_keys]
                category["metadata"] = sorted_data
                categories_data.append(category)

        for data_type, data in deepcopy(metadata.sorted).items():
            carousel_sorted_data = sorted(
                deepcopy(data), key=lambda k: k["popularity"], reverse=True
            )
            carousel_sorted_data = carousel_sorted_data[:3]
            for item in carousel_sorted_data:
                [item.pop(key, None) for key in unwanted_keys]
            carousel_data.extend(carousel_sorted_data)

            top_rated_sort_data = sorted(
                deepcopy(data), key=lambda k: k["rating"], reverse=True
            )
            top_rated_sort_data = top_rated_sort_data[:data_cap_limit]
            for item in top_rated_sort_data:
                [item.pop(key, None) for key in unwanted_keys]
            if data_type == "movies":
                top_rated_movies_data.extend(top_rated_sort_data)
                new_movies_sort_data = sorted(
                    deepcopy(data), key=lambda k: k["modified_time"], reverse=True
                )
                new_movies_sort_data = new_movies_sort_data[:data_cap_limit]
                for item in new_movies_sort_data:
                    [item.pop(key, None) for key in unwanted_keys]
                newly_added_movies_data.extend(new_movies_sort_data)
            elif data_type == "series":
                top_rated_series_data.extend(top_rated_sort_data)
                all_episodes = []
                for item in data:
                    for season in item["seasons"]:
                        for episode in season["episodes"]:
                            episode.update(
                                {
                                    "season_number": season["season_number"],
                                    "series_id": item["id"],
                                    "series_name": item["title"],
                                    "series_poster": item["poster_url"],
                                    "season_name": season["name"],
                                    "season_poster": season["poster_path"],
                                    "tmdb_id": item["tmdb_id"],
                                }
                            )
                            all_episodes.append(episode)
                newly_added_episodes_sort_data = sorted(
                    deepcopy(all_episodes),
                    key=lambda k: k.get("air_date") or "",
                    reverse=True,
                )
                newly_added_episodes_data = newly_added_episodes_sort_data[
                    :data_cap_limit
                ]
        random.shuffle(carousel_data)

        cache.set("home_route_data", dict(
            categories_data=categories_data,
            carousel_data=carousel_data,
            top_rated_series_data=top_rated_series_data,
            top_rated_movies_data=top_rated_movies_data,
            newly_added_movies_data=newly_added_movies_data,
            newly_added_episodes_data=newly_added_episodes_data,
        ))
    else:
        logger.debug("Using cached data")
        categories_data = data.get("categories_data")
        carousel_data = data.get("carousel_data")
        top_rated_movies_data = data.get("top_rated_movies_data")
        top_rated_series_data = data.get("top_rated_series_data")
        newly_added_episodes_data = data.get("newly_added_episodes_data")
        newly_added_movies_data = data.get("newly_added_movies_data")
    end = time.perf_counter()
    return {
        "ok": True,
        "message": "success",
        "data": {
            "categories": categories_data,
            "carousel": carousel_data,
            "top_rated_movies": top_rated_movies_data,
            "top_rated_series": top_rated_series_data,
            "newly_added_movies": newly_added_movies_data,
            "newly_added_episodes": newly_added_episodes_data,
        },
        "time_taken": end - start,
    }