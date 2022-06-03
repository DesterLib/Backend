from app.core import TMDB
from app.utils import generate_movie_metadata, generate_series_metadata

from .. import logger


def fetch_metadata(tmdb: TMDB):
    from main import mongo, rclone
    for key, category in rclone.items():
        category_id = category.data.get("id") or category.data.get("drive_id")
        category_metadata = {"id": category_id, "type": category.data.get("type", "movies"), "name": category.data.get(
            "name"), "include_in_homepage": category.data.get("include_in_homepage", True)}
        logger.info("Generating metadata: " + category_metadata["name"])
        logger.debug("Category type: " + category_metadata["type"])
        if category_metadata["type"] == "series":
            generate_series_metadata(
                tmdb, rclone[key].fetch_series(), category_metadata)
        else:
            generate_movie_metadata(
                tmdb, rclone[key].fetch_movies(), category_metadata)
        mongo.set_is_metadata_init(True)
