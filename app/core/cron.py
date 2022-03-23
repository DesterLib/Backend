from typing import List
from app.core import DriveAPI, TMDB
from app.utils import generate_movie_metadata, generate_series_metadata

def fetch_metadata(drive: DriveAPI, tmdb: TMDB, categories: List[str]):
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
            category_metadata["include_in_homepage"] = category.get("include_in_homepage")
            print(f"{category_type=}")
            data = generate_movie_metadata(tmdb, drive.fetch_movies(category_id)) if category_type == "movies" else generate_series_metadata(tmdb, drive.fetch_series(category_id))
            category_metadata["metadata"] = data
            metadata.append(category_metadata)
    return metadata