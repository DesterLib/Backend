from typing import List

from app.core import TMDB, RCloneAPI
from app.utils import generate_movie_metadata, generate_series_metadata


def fetch_metadata(tmdb: TMDB, categories: List[str]):
    print("Generating metadata...")
    metadata = []
    if categories:
        for category in categories:
            category_metadata = {}
            category_id = category.get("id")
            category_type = category.get("type")
            category_metadata["id"] = category_id
            category_metadata["type"] = category_type
            category_metadata["name"] = category.get("name")
            category_metadata["include_in_homepage"] = category.get(
                "include_in_homepage"
            )
            print(f"{category_type=}")
            from main import rclone
            data = (
                generate_movie_metadata(tmdb, rclone[category_id].fetch_movies())
                if category_type == "movies"
                else generate_series_metadata(tmdb, rclone[category_id].fetch_series())
            )
            category_metadata["metadata"] = data
            metadata.append(category_metadata)
    return metadata
