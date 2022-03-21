from functools import reduce
from collections import defaultdict
import re
from typing import Any, Dict
import ujson as json
from app.core import TMDB
from app.models import DataType
from app.settings import settings

def group_by(key, seq):
    return reduce(lambda grp, val: grp[key(val)].append(val) or grp, seq, defaultdict(list))

def parse_filename(name: str, data_type: DataType):
    reg_exps = [
        # (2019) The Mandalorian
        r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*$",
        # The Mandalorian (2019)
        r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*$",
        # The.Mandalorian.2019.1080p.WEBRip
        r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*$",
        # The Mandalorian
        r"^(?P<year>)(?P<title>.*)$" ,
        
    ] if data_type == DataType.series else [
        # (2008) Iron Man.mkv
        r"^[\(\[\{](?P<year>\d{4})[\)\]\}]\s(?P<title>[^.]+).*(?P<extention>\..*)?$",
        # Iron Man (2008).mkv
        r"^(?P<title>.*)\s[\(\[\{](?P<year>\d{4})[\)\]\}].*(?P<extention>\..*)?$",
        # Iron.Man.2008.1080p.WEBRip.DDP5.1.Atmos.x264.mkv
        # r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*(?P<extention>\..*)?$",
        r"^(?P<title>(?:(?!\.\d{4}).)*)\.(?P<year>\d{4}).*?(?P<extention>\.\w+)?$",
        # Iron Man.mkv
        r"^(?P<year>)(?P<title>.*).*(?P<extention>\..*?)?"
    ]
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
        r'\(?(?:240|360|480|720|1080|1440|2160)p?\)?', # 1080p, 720p, etc
        r'\((?:\D.+?|.+?\D)\)|\[(?:\D.+?|.+?\D)\]', # (2016), [2016], etc
        r'\b(?:mp4|mkv|wmv|m4v|mov|avi|flv|webm|flac|mka|m4a|aac|ogg)\b', # file types
        r'season ?\d+?', # season 1, season 2, etc
    ]
    for reg in reg_exps:
        name = re.sub(reg, '', name, flags=re.I)
    return name.strip()

def generate_movie_metadata(tmdb: TMDB, data: Dict[str, Any]) -> Dict[str, Any]:
    metadata = []
    for drive_meta in data:
        original_name = drive_meta["name"] 
        print("original file name: ", original_name)
        cleaned_title = clean_file_name(original_name)
        print(f"{cleaned_title=}")
        name_year = parse_filename(cleaned_title, DataType.movie)
        name = name_year.get("title")
        year = name_year.get("year")
        print("name: ", name)
        tmdb_id = tmdb.find_media_id(name, DataType.movie)
        if not tmdb_id:
            print("Could not find movie id for: ", name)
            print("Skipping...")
            continue
        print("Found: ", name, f"({year})", f" ID:{tmdb_id}")
        movie_info = tmdb.get_details(tmdb_id, DataType.movie)
        try:
            logo = movie_info.get("images", {}).get("logos", [{}])[0].get("file_path")
        except IndexError:
            logo = None
        metadata.append(
            dict(
                id=drive_meta.get("id"),
                tmdb_id=movie_info.get("id"),
                imdb_id=movie_info.get("imdb_id"),
                file_name=drive_meta.get("name"),
                original_title=movie_info.get("original_title"),
                title=movie_info.get("title"),
                status=movie_info.get("status"),
                homepage=movie_info.get("homepage"),
                logo=logo,
                modified_time=drive_meta.get("modifiedTime"),
                video_metadata=drive_meta.get("videoMediaMetadata"),
                content_hints=drive_meta.get("contentHints"),
                thumbnail_path=f"{settings.API_V1_STR}/assets/thumbnail/{drive_meta['id']}" if drive_meta.get("hasThumbnail") else None,
                popularity=movie_info.get("popularity"),
                revenue=movie_info.get("revenue"),
                rating=movie_info.get("vote_average"),
                release_date=movie_info.get("release_date"),
                year=movie_info.get("release_date", "").split("-")[0] or None,
                tagline=movie_info.get("tagline"),
                description=movie_info.get("overview"),
                cast=movie_info.get("credits", {}).get("cast", []),
                backdrop_url=movie_info.get("backdrop_path"),
                collection=movie_info.get("belongs_to_collection"),
                poster_url=movie_info.get("poster_path"),
                genres=movie_info.get("genres"),
                subtitles=drive_meta.get("subtitles"),
                external_ids=movie_info.get("external_ids"),
            )
        )
    return metadata

def generate_series_metadata(tmdb: TMDB, data: Dict[str, Any]) -> Dict[str, Any]:
    metadata = []
    for drive_meta in data:
        original_name = drive_meta["name"] 
        print("original file name: ", original_name)
        cleaned_title = clean_file_name(original_name)
        print(f"{cleaned_title=}")
        name_year = parse_filename(cleaned_title, DataType.series)
        name = name_year.get("title")
        year = name_year.get("year")
        print("Regex matched: ", name, f"({year})" if year else "")
        tmdb_id = tmdb.find_media_id(name, DataType.series)
        if not tmdb_id:
            print("Could not find series id for: ", name)
            print("Skipping...")
            continue
        print("TMDB ID: ", tmdb_id)
        series_info = tmdb.get_details(tmdb_id, DataType.series)
        seasons=series_info.get("seasons", [])
        print("Seasons: ", len(seasons))
        
        try:
            logo = series_info.get("images", {}).get("logos", [{}])[0].get("file_path")
        except:
            logo = None
        
        for season in seasons:
            season["episodes"] = drive_meta.get("seasons", {}).get(str(season.get('season_number')), {}).get("episodes", [])
            print(f"    Episodes in {season.get('name')} = ", len(season["episodes"]))
            for count, episode in enumerate(season["episodes"]):
                print("        "+episode["name"])
                parsed_data = parse_episode_filename(episode["name"])
                episode_number = parsed_data.get("episode")
                season_number = parsed_data.get("season")
                if season_number != season.get("season_number"):
                    print(f"            Season number mismatch: {season_number} != {season.get('season_number')}")
                if not episode_number:
                    episode_number = count + 1
                episode_details = tmdb.get_episode_details(tmdb_id, episode_number, season_number)
                if not episode_details:
                    episode_details = {
                        "name": None,
                        "air_date": f"{year}-01-01" if year else None,
                        "episode_number": episode_number,
                        "overview": None,
                        "still_path": None,
                        "vote_average": None,
                        "vote_count": None,
                    }
                episode_details.pop("id", None)
                episode_details.pop("crew", None)
                episode_details.pop("guest_stars", None)
                episode_details.pop("production_code", None)
                episode_details.pop("season_number", None)
                episode.update(episode_details)
                    
        metadata.append(
            dict(
                id=drive_meta.get("id"),
                tmdb_id=series_info.get("id"),
                file_name=drive_meta.get("name"),
                original_title=series_info.get("original_name"),
                title=series_info.get("name"),
                status=series_info.get("status"),
                total_episodes=series_info.get("number_of_episodes"),
                total_seasons=series_info.get("number_of_seasons"),
                homepage=series_info.get("homepage"),
                logo=logo,
                popularity=series_info.get("popularity"),
                revenue=series_info.get("revenue"),
                rating=series_info.get("vote_average"),
                year=series_info.get("first_air_date", "").split("-")[0] or None,
                first_air_date=series_info.get("first_air_date"),
                last_air_date=series_info.get("last_air_date"),
                tagline=series_info.get("tagline"),
                description=series_info.get("overview"),
                seasons=seasons,
                last_episode_to_air=series_info.get("last_episode_to_air"),
                next_episode_to_air=series_info.get("next_episode_to_air"),
                cast=series_info.get("credits", {}).get("cast", []),
                backdrop_url=series_info.get("backdrop_path"),
                poster_url=series_info.get("poster_path"),
                genres=series_info.get("genres"),
                subtitles=drive_meta.get("subtitles"),
                external_ids=series_info.get("external_ids"),
            )
        )
    return metadata