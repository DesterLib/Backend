import re
from .. import logger
from typing import Any, Dict
from datetime import datetime
from dateutil.parser import isoparse


class Episode:
    def __init__(self, file_metadata, media_metadata, index):
        # File Info
        self.id: str = file_metadata.get("id") or ""
        self.file_name: str = file_metadata.get("name") or ""
        self.path: str = file_metadata.get("path") or ""
        self.parent: dict = file_metadata.get("parent") or {}
        self.modified_time: datetime = isoparse(
            file_metadata.get("modifiedTime", "1900-03-27T00:00:00.000+00:00")
        )

        parsed_data = self.parse_episode_filename(self.file_name)
        episode_number = parsed_data.get("episode")
        season_number = parsed_data.get("season", media_metadata.get("season_number"))
        if season_number != media_metadata.get("season_number"):
            logger.debug(
                f"      Season number mismatch: {season_number} != {media_metadata.get('season_number')}"
            )
        if not episode_number:
            episode_number = index
        try:
            episode_metadata = media_metadata["episodes"][episode_number - 1]
        except IndexError:
            episode_metadata = {}

        # Media Info
        self.tmdb_id: int = episode_metadata.get("id") or 0
        self.name: str = episode_metadata.get("name") or ""
        self.overview: str = episode_metadata.get("overview") or ""
        air_date: str = media_metadata.get("air_date") or "1900-03-27"
        self.air_date: datetime = datetime.strptime(air_date, "%Y-%m-%d")
        self.runtime: int = episode_metadata.get("runtime") or 0
        self.episode_number: int = episode_metadata.get("season_number") or 0
        self.rating: float = episode_metadata.get("vote_average") or 0

        # Media Resources
        self.thumbnail_path: str = episode_metadata.get("still_path") or ""

    def parse_episode_filename(self, name: str) -> Dict[str, Any]:
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
