import random
import time
from copy import deepcopy
from typing import Dict, Union

from fastapi import APIRouter

router = APIRouter(
    # dependencies=[Depends(get_token_header)],
    prefix="/home",
    responses={404: {"description": "Not found"}},
    tags=["internals"],
)

data_cap_limit = 15


@router.get("", response_model=Dict[str, Union[str, int, float, bool, None, dict]])
def home() -> Dict[str, str]:
    start = time.perf_counter()
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
                category["metadata"], key=lambda k: k["popularity"], reverse=True
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
                deepcopy(all_episodes), key=lambda k: k["air_date"], reverse=True
            )
            newly_added_episodes_data = newly_added_episodes_sort_data[:data_cap_limit]
    random.shuffle(carousel_data)
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
