import re
from collections import defaultdict
from copy import deepcopy
from functools import reduce
from typing import Any, Dict, Optional

from app import logger
from app.models import DataType
from app.settings import settings
from pymongo import TEXT, InsertOne

from .. import logger


def group_by(key, seq):
    return reduce(
        lambda grp, val: grp[key(val)].append(
            val) or grp, seq, defaultdict(list)
    )


def try_int(value: str) -> Optional[int]:
    try:
        value = int(value)
    except ValueError:
        value = None
    return value


def sort_by_type(metadata: Dict[str, Any] = {}) -> Dict[str, Any]:
    data = {"movies": [], "series": []}
    ids = deepcopy(data)
    for category in metadata:
        meta = category["metadata"]
        for item in meta:
            item["category"] = {
                "id": category.get("id") or category.get("drive_id"),
                "name": category["name"],
            }
            if category["type"] == "movies":
                if not item["tmdb_id"] in ids["movies"]:
                    data["movies"].append(item)
            elif category["type"] == "series":
                if not item["tmdb_id"] in ids["series"]:
                    data["series"].append(item)
            ids[category.get("type")].append(item["tmdb_id"])
    return data


def parse_filename(name: str, data_type: DataType):
    reg_exps = (
        [
            # (2019) The Mandalorian
            r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*$",
            # The Mandalorian (2019)
            r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*$",
            # The.Mandalorian.2019.1080p.WEBRip
            r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*$",
            # The Mandalorian
            r"^(?P<year>)(?P<title>.*)$",
        ]
        if data_type == DataType.series
        else [
            # (2008) Iron Man.mkv
            r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*(?P<extention>\..*)?$",
            # Iron Man (2008).mkv
            r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*(?P<extention>\..*)?$",
            # Iron.Man.2008.1080p.WEBRip.DDP5.1.Atmos.x264.mkv
            # r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*(?P<extention>\..*)?$",
            r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*?(?P<extention>\.\w+)?$",
            # Iron Man.mkv
            r"^(?P<year>)(?P<title>.*).*(?P<extention>\..*?)?",
        ]
    )
    for exp in reg_exps:
        if match := re.match(exp, name):
            data = match.groupdict()
            data["title"] = data["title"].strip().replace(".", " ")
            return data
    else:
        return {}


def parse_episode_filename(name: str):
    reg_exps = [
        r".+?s ?(?P<season>\d{0,2})e ?(?P<episode>\d{0,4}).+",
        r".+?e ?(?P<episode>\d{0,2})s ?(?P<season>\d{0,4}).+",
        r".+?e ?(?P<episode>\d{0,4})",
    ]
    for exp in reg_exps:
        if match := re.match(exp, name, flags=2):
            data = match.groupdict()
            if not data.get("season"):
                data["season"] = 1
            if data.get("episode"):
                data["episode"] = int(data["episode"])
            data["season"] = int(data["season"])
            return data
    else:
        return {}


def clean_file_name(name: str) -> str:
    reg_exps = [
        r"\((?:\D.+?|.+?\D)\)|\[(?:\D.+?|.+?\D)\]",  # (2016), [2016], etc
        r"\(?(?:240|360|480|720|1080|1440|2160)p?\)?",  # 1080p, 720p, etc
        r"\b(?:mp4|mkv|wmv|m4v|mov|avi|flv|webm|flac|mka|m4a|aac|ogg)\b",  # file types
        r"season ?\d+?",  # season 1, season 2, etc
        # more stuffs
        r"(?:S\d{1,3}|\d+?bit|dsnp|web\-dl|ddp\d+? ? \d|hevc|hdrip|\-?Vyndros)",
        # URLs in filenames
        r"^(?:https?:\/\/)?(?:www.)?[a-z0-9]+\.[a-z]+(?:\/[a-zA-Z0-9#]+\/?)*$",
    ]
    for reg in reg_exps:
        name = re.sub(reg, "", name, flags=re.I)
    return name.strip().rstrip(".-_")


def generate_movie_metadata(tmdb, data: Dict[str, Any], category_metadata: Dict[str, Any]) -> Dict[str, Any]:
    from main import mongo

    metadata = mongo.metadata[category_metadata["id"]]
    advanced_search_list = []
    mongo_meta = []
    for drive_meta in data:
        original_name = drive_meta["name"]
        cleaned_title = clean_file_name(original_name)
        logger.debug(f"Identifying: {cleaned_title}")
        name_year = parse_filename(cleaned_title, DataType.movies)
        name = name_year.get("title")
        year = name_year.get("year")
        tmdb_id = tmdb.find_media_id(name, DataType.movies)
        if not tmdb_id:
            advanced_search_list.append((name, year))
            logger.info(f"Could not identify: {name}")
            logger.debug("Skipping and adding to the advanced search list...")
            continue
        logger.info(
            f"Successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        movie_info = tmdb.get_details(tmdb_id, DataType.movies)
        try:
            logo = movie_info.get("images", {}).get(
                "logos", [{}])[0].get("file_path")
        except IndexError:
            logo = None
        curr_metadata = (
            {
                "id": drive_meta["id"],
                "path": drive_meta["path"],
                "tmdb_id": movie_info["id"],
                "imdb_id": movie_info.get("imdb_id"),
                "file_name": drive_meta["name"],
                "original_title": movie_info.get("original_title"),
                "title": movie_info.get("title"),
                "status": movie_info.get("status"),
                "homepage": movie_info.get("homepage"),
                "logo": logo,
                "modified_time": drive_meta["modifiedTime"],
                "video_metadata": drive_meta.get("videoMediaMetadata"),
                "thumbnail_path": f"{settings.API_V1_STR}/assets/thumbnail/{drive_meta['id']}",
                "popularity": movie_info.get("popularity"),
                "revenue": movie_info.get("revenue"),
                "rating": movie_info.get("vote_average"),
                "release_date": movie_info.get("release_date"),
                "year": try_int(movie_info.get("release_date", "").split("-")[0])
                or None,
                "tagline": movie_info.get("tagline"),
                "description": movie_info.get("overview"),
                "cast": movie_info.get("credits", {}).get("cast", []),
                "backdrop_url": movie_info.get("backdrop_path"),
                "collection": movie_info.get("belongs_to_collection"),
                "poster_url": movie_info.get("poster_path"),
                "genres": movie_info.get("genres"),
                "subtitles": drive_meta["subtitles"],
                "external_ids": movie_info.get("external_ids"),
            }
        )
        update_action = InsertOne(curr_metadata)
        mongo_meta.append(update_action)
    logger.debug(
        f"Using advanced search for {len(advanced_search_list)} titles.")
    for name, year in advanced_search_list:
        logger.debug(f"Advanced search identifying: {cleaned_title}")
        tmdb_id = tmdb.find_media_id(name, DataType.movies, use_api=False)
        if not tmdb_id:
            logger.info(f"Advanced search could not identify: '{name}'")
            continue
        logger.info(
            f"Advanced search successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        movie_info = tmdb.get_details(tmdb_id, DataType.movies)
        try:
            logo = movie_info.get("images", {}).get(
                "logos", [{}])[0].get("file_path")
        except IndexError:
            logo = None
        curr_metadata = (
            {
                "id": drive_meta["id"],
                "path": drive_meta["path"],
                "tmdb_id": movie_info["id"],
                "imdb_id": movie_info.get("imdb_id"),
                "file_name": drive_meta["name"],
                "original_title": movie_info.get("original_title"),
                "title": movie_info.get("title"),
                "status": movie_info.get("status"),
                "homepage": movie_info.get("homepage"),
                "logo": logo,
                "modified_time": drive_meta["modifiedTime"],
                "video_metadata": drive_meta.get("videoMediaMetadata"),
                "thumbnail_path": f"{settings.API_V1_STR}/assets/thumbnail/{drive_meta['id']}",
                "popularity": movie_info.get("popularity"),
                "revenue": movie_info.get("revenue"),
                "rating": movie_info.get("vote_average"),
                "release_date": movie_info.get("release_date"),
                "year": try_int(movie_info.get("release_date", "").split("-")[0])
                or None,
                "tagline": movie_info.get("tagline"),
                "description": movie_info.get("overview"),
                "cast": movie_info.get("credits", {}).get("cast", []),
                "backdrop_url": movie_info.get("backdrop_path"),
                "collection": movie_info.get("belongs_to_collection"),
                "poster_url": movie_info.get("poster_path"),
                "genres": movie_info.get("genres"),
                "subtitles": drive_meta["subtitles"],
                "external_ids": movie_info.get("external_ids"),
            }
        )
        update_action = InsertOne(curr_metadata)
        mongo_meta.append(update_action)

    metadata.delete_many({})
    metadata.bulk_write(mongo_meta)
    metadata.create_index([("title", TEXT)],
                          background=True, name="title")
    return metadata


def generate_series_metadata(tmdb, data: Dict[str, Any], category_metadata: Dict[str, Any]) -> Dict[str, Any]:
    from main import mongo

    metadata = mongo.metadata[category_metadata["id"]]
    mongo_meta = []
    for drive_meta in data:
        original_name = drive_meta["name"]
        cleaned_title = clean_file_name(original_name)
        logger.debug(f"Identifying: {cleaned_title}")
        name_year = parse_filename(cleaned_title, DataType.series)
        name = name_year.get("title")
        year = name_year.get("year")
        tmdb_id = tmdb.find_media_id(name, DataType.series)
        if not tmdb_id:
            tmdb_id = tmdb.find_media_id(name, DataType.series, use_api=False)
            if not tmdb_id:
                logger.info(f"Could not identify: '{name}'")
                continue
        logger.info(
            f"Successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        series_info = tmdb.get_details(tmdb_id, DataType.series)
        if series_info.get("first_air_date") is None:
            series_info["first_air_date"] = ""
        seasons = series_info.get("seasons", [])
        logger.info(f"Number of seasons: {len(seasons)}")

        try:
            logo = series_info.get("images", {}).get(
                "logos", [{}])[0].get("file_path")
        except BaseException:
            logo = None

        for season in seasons:
            season["episodes"] = (
                drive_meta.get("seasons", {})
                .get(str(season.get("season_number")), {})
                .get("episodes", [])
            )
            logger.info(
                f"   {season.get('name')}: {len(season.get('episodes', 0))} episodes"
            )
            for count, episode in enumerate(season["episodes"]):
                logger.debug(f"     {episode['name']}")
                parsed_data = parse_episode_filename(episode["name"])
                episode_number = parsed_data.get("episode")
                season_number = parsed_data.get(
                    "season", season.get("season_number"))
                if season_number != season.get("season_number"):
                    logger.debug(
                        f"      Season number mismatch: {season_number} != {season.get('season_number')}"
                    )
                if not episode_number:
                    episode_number = len(season["episodes"]) - count
                try:
                    episode_details = series_info[f"season/{season_number}"][
                        "episodes"
                    ][episode_number - 1]
                except IndexError:
                    episode_details = {
                        "name": None,
                        "air_date": f"{year}-01-01" if year else None,
                        "episode_number": episode_number,
                        "overview": None,
                        "still_path": None,
                        "rating": None,
                        "vote_count": None,
                    }
                episode_details.pop("id", None)
                episode_details.pop("crew", None)
                episode_details.pop("guest_stars", None)
                episode_details.pop("production_code", None)
                episode_details.pop("season_number", None)
                episode.update(episode_details)
                episode["episode_thumbnail"] = episode.pop("still_path", None)

        curr_metadata = (
            {
                "id": drive_meta.get("id"),
                "path": drive_meta["path"],
                "tmdb_id": series_info.get("id"),
                "file_name": drive_meta.get("name"),
                "original_title": series_info.get("original_name"),
                "title": series_info.get("name"),
                "status": series_info.get("status"),
                "total_episodes": series_info.get("number_of_episodes"),
                "total_seasons": series_info.get("number_of_seasons"),
                "homepage": series_info.get("homepage"),
                "logo": logo,
                "popularity": series_info.get("popularity"),
                "revenue": series_info.get("revenue"),
                "rating": series_info.get("vote_average"),
                "year": try_int(series_info.get(
                    "first_air_date", "").split("-")[0])
                or None,
                "first_air_date": series_info.get("first_air_date"),
                "release_date": series_info.get("first_air_date"),
                "last_air_date": series_info.get("last_air_date"),
                "tagline": series_info.get("tagline"),
                "description": series_info.get("overview"),
                "seasons": seasons,
                "last_episode_to_air": series_info.get("last_episode_to_air"),
                "next_episode_to_air": series_info.get("next_episode_to_air"),
                "cast": series_info.get("credits", {}).get("cast", []),
                "backdrop_url": series_info.get("backdrop_path"),
                "poster_url": series_info.get("poster_path"),
                "genres": series_info.get("genres"),
                "subtitles": drive_meta.get("subtitles"),
                "external_ids": series_info.get("external_ids"),
            }
        )
        update_action = InsertOne(curr_metadata)
        mongo_meta.append(update_action)

    metadata.delete_many({})
    metadata.bulk_write(mongo_meta)
    metadata.create_index([("title", TEXT)],
                          background=True, name="title")
    return metadata
