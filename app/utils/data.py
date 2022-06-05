import re
from app import logger
from copy import deepcopy
from functools import reduce
from app.models import Movie, Serie
from collections import defaultdict
from typing import Any, Dict, Optional
from pymongo import TEXT, DESCENDING, InsertOne


def group_by(key, seq):
    return reduce(
        lambda grp, val: grp[key(val)].append(val) or grp, seq, defaultdict(list)
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


def parse_filename(name: str, data_type: str):
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
        if data_type == "series"
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


def generate_movie_metadata(
    tmdb, data: Dict[str, Any], category_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    from main import mongo

    metadata = mongo.metadata[category_metadata["id"]]
    advanced_search_list = []
    identified_list: Dict[int, Movie] = {}
    for drive_meta in data:
        original_name = drive_meta["name"]
        cleaned_title = clean_file_name(original_name)
        logger.debug(f"Identifying: {cleaned_title}")
        name_year = parse_filename(cleaned_title, "movies")
        name = name_year.get("title")
        year = name_year.get("year")
        tmdb_id = tmdb.find_media_id(name, "movies")
        if not tmdb_id:
            advanced_search_list.append((name, year))
            logger.info(f"Could not identify: {name}")
            logger.debug("Skipping and adding to the advanced search list...")
            continue
        logger.info(
            f"Successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        identified_match = identified_list.get(tmdb_id)
        if identified_match:
            identified_match.append_file(drive_meta)
        else:
            movie_info = tmdb.get_details(tmdb_id, "movies")
            curr_metadata: Movie = Movie(drive_meta, movie_info)
            identified_list[tmdb_id] = curr_metadata
    logger.debug(f"Using advanced search for {len(advanced_search_list)} titles.")
    for name, year in advanced_search_list:
        logger.debug(f"Advanced search identifying: {cleaned_title}")
        tmdb_id = tmdb.find_media_id(name, "movies", use_api=False)
        if not tmdb_id:
            logger.info(f"Advanced search could not identify: '{name}'")
            continue
        logger.info(
            f"Advanced search successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        identified_match = identified_list.get(tmdb_id)
        if identified_match:
            identified_match.append_file(drive_meta)
        else:
            movie_info = tmdb.get_details(tmdb_id, "movies")
            curr_metadata: Movie = Movie(drive_meta, movie_info)
            identified_list[tmdb_id] = curr_metadata

    del movie_info
    mongo_meta = []
    for item in identified_list.values():
        mongo_meta.append(InsertOne(item.__dict__))
    del identified_list
    metadata.delete_many({})
    metadata.bulk_write(mongo_meta)
    metadata.create_index([("title", TEXT)], background=True, name="title")
    return metadata


def generate_series_metadata(
    tmdb, data: Dict[str, Any], category_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    from main import mongo

    metadata = mongo.metadata[category_metadata["id"]]
    mongo_meta = []
    for drive_meta in data:
        original_name = drive_meta["name"]
        cleaned_title = clean_file_name(original_name)
        logger.debug(f"Identifying: {cleaned_title}")
        name_year = parse_filename(cleaned_title, "series")
        name = name_year.get("title")
        year = name_year.get("year")
        tmdb_id = tmdb.find_media_id(name, "series")
        if not tmdb_id:
            tmdb_id = tmdb.find_media_id(name, "series", use_api=False)
            if not tmdb_id:
                logger.info(f"Could not identify: '{name}'")
                continue
        logger.info(
            f"Successfully identified: {name} {f'({year})' if year else ''}    ID: {tmdb_id}"
        )
        series_info = tmdb.get_details(tmdb_id, "series")
        curr_metadata: Serie = Serie(drive_meta, series_info)
        update_action = InsertOne(curr_metadata.__dict__)
        mongo_meta.append(update_action)

    del series_info
    del curr_metadata
    metadata.delete_many({})
    metadata.bulk_write(mongo_meta)
    metadata.create_index([("title", TEXT)], background=True, name="title")
    metadata.create_index(
        [("seasons.episodes.modified_time", DESCENDING)],
        background=True,
        name="modified_time",
    )
    return metadata
