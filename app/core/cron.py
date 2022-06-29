from app import logger
from app.core.tmdb import TMDB
from app.apis import mongo, rclone
from pymongo import TEXT, DESCENDING
from app.utils import generate_movie_metadata, generate_series_metadata


def fetch_metadata():
    """Generates the metadata for each category"""

    tmdb = TMDB(api_key=mongo.config["tmdb"]["api_key"])
    series_metadata = []
    movies_metadata = []
    for key, category in rclone.items():
        logger.info("Generating metadata: %s", category.data.get("name"))
        if category.data.get("type", "movies") == "series":
            series_metadata.extend(
                generate_series_metadata(tmdb, rclone[key].fetch_series(), key)
            )
        else:
            movies_metadata.extend(
                generate_movie_metadata(tmdb, rclone[key].fetch_movies(), key)
            )
    mongo.movies_col.delete_many({})
    if len(movies_metadata) > 0:
        mongo.movies_col.bulk_write(movies_metadata)
    mongo.movies_col.create_index([("title", TEXT)], background=True, name="title")
    mongo.series_col.delete_many({})
    if len(series_metadata) > 0:
        mongo.series_col.bulk_write(series_metadata)
    mongo.series_col.create_index([("title", TEXT)], background=True, name="title")
    mongo.series_col.create_index(
        [("seasons.episodes.modified_time", DESCENDING)],
        background=True,
        name="modified_time",
    )
    mongo.set_is_metadata_init(True)

    logger.info(
        "METADATA BUILDING COMPLETE! %s movies and %s series identified.",
        len(movies_metadata),
        len(series_metadata),
    )
