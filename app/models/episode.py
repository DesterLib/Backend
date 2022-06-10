import re
from app import logger
from datetime import datetime
from dateutil.parser import isoparse


class Episode:
    __slots__ = [
        "id",
        "file_name",
        "path",
        "parent",
        "modified_time",
        "tmdb_id",
        "name",
        "overview",
        "air_date",
        "episode_number",
        "rating",
        "thumbnail_path",
    ]

    def __dict__(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "path": self.path,
            "parent": self.parent,
            "modified_time": self.modified_time,
            "tmdb_id": self.tmdb_id,
            "name": self.name,
            "overview": self.overview,
            "air_date": self.air_date,
            "episode_number": self.episode_number,
            "rating": self.rating,
            "thumbnail_path": self.thumbnail_path,
        }

    def __init__(self, file_metadata, media_metadata, index):
        # File Info
        self.id: str = file_metadata["id"]
        self.file_name: str = file_metadata["name"]
        self.path: str = file_metadata["path"]
        self.parent: dict = file_metadata["parent"]
        self.modified_time: datetime = isoparse(file_metadata["modified_time"])

        parsed_data = self.parse_episode_filename(self.file_name)
        try:
            episode_number = int(parsed_data["episode"])
        except (KeyError, ValueError):
            episode_number = index
        try:
            season_number = parsed_data["season"]
        except KeyError:
            season_number = media_metadata["season_number"]
        if season_number != media_metadata["season_number"]:
            logger.debug(
                f"      Season number mismatch: {season_number} != {media_metadata['season_number']}"
            )
        try:
            episode_metadata = media_metadata["episodes"][episode_number - 1]
        except IndexError:
            episode_metadata = {
                "id": "",
                "name": self.file_name,
                "overview": "",
                "air_date": "1900-01-01",
                "episode_number": episode_number,
                "vote_average": 0,
                "still_path": "",
            }

        # Media Info
        self.tmdb_id: int = episode_metadata["id"]
        self.name: str = episode_metadata["name"]
        self.overview: str = episode_metadata["overview"]
        air_date: str = media_metadata["air_date"]
        self.air_date: datetime = datetime.strptime(air_date, "%Y-%m-%d")
        self.episode_number: int = episode_number
        self.rating: float = episode_metadata["vote_average"]

        # Media Resources
        self.thumbnail_path: str = episode_metadata["still_path"]

    def parse_episode_filename(self, name: str) -> dict:
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
