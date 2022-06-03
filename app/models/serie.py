from datetime import datetime
from typing import Any, Dict, List

from dateutil.parser import isoparse

from ..settings import settings
from .season import Season


class Serie:
    def __init__(self, file_metadata, media_metadata):
        # File Info
        self.id: str = file_metadata.get("id") or ""
        self.file_name: str = file_metadata.get("name") or ""
        self.path: str = file_metadata.get("path") or ""
        self.parent: dict = file_metadata.get("parent") or {}
        self.modified_time: datetime = isoparse(file_metadata.get(
            "modified_time", "1900-03-27T00:00:00.000+00:00"))

        # Media Info
        self.tmdb_id: int = media_metadata.get("id") or 0
        self.imdb_id: str = media_metadata.get("imdb_id") or ""
        self.title: str = media_metadata.get("title") or ""
        self.original_title: str = media_metadata.get("original_title") or ""
        self.status: str = media_metadata.get("status") or ""
        self.popularity: float = media_metadata.get("popularity") or 0
        self.revenue: int = media_metadata.get("revenue") or 0
        self.rating: float = media_metadata.get("vote_average") or 0
        release_date: str = media_metadata.get("first_air_date") or "1900-03-27"
        self.release_date: datetime = datetime.strptime(release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata.get("tagline") or ""
        self.description: str = media_metadata.get("overview") or ""
        self.cast: List[Dict[str, Any]] = media_metadata.get(
            "credits", {}).get("cast") or []
        self.collection: Dict[str, Any] = media_metadata.get(
            "belongs_to_collection") or {}
        self.genres: List[Dict[str, Any]] = media_metadata.get("genres") or []
        self.external_ids: Dict[str, str] = media_metadata.get(
            "external_ids") or {}
        self.total_episodes: int = media_metadata.get(
            "number_of_episodes") or 0
        self.total_seasons: int = media_metadata.get("number_of_seasons") or 0
        self.last_episode_to_air: Dict[str, Any] = media_metadata.get(
            "last_episode_to_air") or {}
        self.next_episode_to_air: Dict[str, Any] = media_metadata.get(
            "next_episode_to_air") or {}

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata.get("homepage") or ""
        self.thumbnail_path: str = f"{settings.API_V1_STR}/assets/thumbnail/{self.id}"
        self.backdrop_path: str = media_metadata.get("backdrop_path") or ""
        self.poster_path: str = media_metadata.get("poster_path") or ""

        # Seasons
        self.seasons: List[Season] = []
        for season in media_metadata.get("seasons") or []:
            self.seasons.append(Season(file_metadata.get("seasons", {}).get(
                str(season.get("season_number")), {}), media_metadata.get("season/%s" % season.get("season_number", "1"), {})).__dict__)

    def get_logo(self, media_metadata) -> str:
        logo: str = ""
        try:
            logo = media_metadata.get("images", {}).get(
                "logos", [{}])[0].get("file_path") or ""
        except BaseException:
            pass
        return logo
