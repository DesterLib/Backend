import regex as re
from app import logger
from pymongo import InsertOne
from typing import Dict, List
from app.models import Movie, Serie


def parse_filename(name: str, data_type: str):
    """Identifies media names and years from file name"""
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
    return {}


def clean_file_name(name: str) -> str:
    """Removes common and unnecessary strings from file names"""
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
        name = re.sub(reg, "", name)
    return name.strip().rstrip(".-_")


def generate_movie_metadata(tmdb, data: dict, rclone_index: int) -> List[InsertOne]:
    """Matches and identifies movies by file names and returns a list of MongoDB insert tasks"""
    advanced_search_list = []
    identified_list: Dict[int, Movie] = {}
    for drive_meta in data:
        original_name = drive_meta["name"]
        match = re.search(r"{{(tmdb_id|anidb_id):(\d{1,8})}}", original_name)
        if match:
            tmdb_id = match.group(2)
        else:
            cleaned_title = clean_file_name(original_name)
            name_year = parse_filename(cleaned_title, "movies")
            name = name_year.get("title")
            year = name_year.get("year")
            tmdb_id = tmdb.find_media_id(name, "movies", year=year)
        if not tmdb_id:
            advanced_search_list.append((name, year))
            logger.info("Could not identify: %s", name)
            continue
        logger.info(
            "Successfully identified: %s %s    ID: %s",
            name,
            "year" if year else "",
            tmdb_id,
        )
        identified_match = identified_list.get(tmdb_id)
        if identified_match:
            identified_match.append_file(drive_meta)
        else:
            movie_info = tmdb.get_details(tmdb_id, "movies")
            curr_metadata: Movie = Movie(drive_meta, movie_info, rclone_index)
            identified_list[tmdb_id] = curr_metadata
    for name, year in advanced_search_list:
        logger.debug("Advanced search identifying: %s", cleaned_title)
        tmdb_id = tmdb.find_media_id(name, "movies", year=year, use_api=False)
        if not tmdb_id:
            logger.info("Advanced search could not identify: %s", name)
            continue
        identified_match = identified_list.get(tmdb_id)
        if identified_match:
            identified_match.append_file(drive_meta)
        else:
            movie_info = tmdb.get_details(tmdb_id, "movies")
            logger.info(
                "Successfully identified: %s    ID: %s", movie_info["title"], tmdb_id
            )
            curr_metadata: Movie = Movie(drive_meta, movie_info, rclone_index)
            identified_list[tmdb_id] = curr_metadata
    metadata: List[InsertOne] = []
    for item in identified_list.values():
        metadata.append(InsertOne(item.__json__()))
    return metadata


def generate_series_metadata(tmdb, data: dict, rclone_index: int) -> List[InsertOne]:
    """Matches and identifies series by folder names and returns a list of MongoDB insert tasks"""
    metadata: List[InsertOne] = []
    for drive_meta in data:
        original_name = drive_meta["name"]
        match = re.search(r"{{(tmdb_id|anidb_id):(\d{1,8})}}", original_name)
        if match:
            tmdb_id = match.group(2)
        else:
            cleaned_title = clean_file_name(original_name)
            name_year = parse_filename(cleaned_title, "series")
            name = name_year.get("title")
            year = name_year.get("year")
            tmdb_id = tmdb.find_media_id(name, "series", year=year)
        if not tmdb_id:
            tmdb_id = tmdb.find_media_id(name, "series", year=year, use_api=False)
            if not tmdb_id:
                logger.info("Could not identify: %s", name)
                continue
        series_info = tmdb.get_details(tmdb_id, "series")
        logger.info(
            "Successfully identified: %s    ID: %s", series_info["name"], tmdb_id
        )
        curr_metadata: Serie = Serie(drive_meta, series_info, rclone_index)
        metadata.append(InsertOne(curr_metadata.__json__()))
    return metadata
