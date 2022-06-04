from datetime import datetime
from app.settings import settings
from typing import Any, Dict, List
from dateutil.parser import isoparse


class Movie:
    def __init__(self, file_metadata, media_metadata):
        # File Info
        self.id: List[str] = [file_metadata.get("id") or ""]
        self.file_name: List[str] = [file_metadata.get("name") or ""]
        self.path: List[str] = [file_metadata.get("path") or ""]
        self.parent: List[Dict[str, Any]] = [file_metadata.get("parent") or {}]
        self.modified_time: List[datetime] = [isoparse(
            file_metadata.get("modified_time", "1900-03-27T00:00:00.000+00:00")
        )]
        self.number_of_files: int = 1

        # Media Info
        self.tmdb_id: int = media_metadata.get("id") or 0
        self.imdb_id: str = media_metadata.get("imdb_id") or ""
        self.title: str = media_metadata.get("title") or ""
        self.original_title: str = media_metadata.get("original_title") or ""
        self.status: str = media_metadata.get("status") or ""
        self.popularity: float = media_metadata.get("popularity") or 0
        self.revenue: int = media_metadata.get("revenue") or 0
        self.rating: float = media_metadata.get("vote_average") or 0
        release_date: str = media_metadata.get("release_date") or "1900-03-27"
        self.release_date: datetime = datetime.strptime(
            release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata.get("tagline") or ""
        self.description: str = media_metadata.get("overview") or ""
        self.cast: List[Dict[str, Any]] = (
            media_metadata.get("credits", {}).get("cast") or []
        )
        self.crew: List[Dict[str, Any]] = (
            media_metadata.get("credits", {}).get("crew") or []
        )
        self.collection: Dict[str, Any] = (
            media_metadata.get("belongs_to_collection") or {}
        )
        self.genres: List[Dict[str, Any]] = media_metadata.get("genres") or []
        self.external_ids: Dict[str, str] = media_metadata.get(
            "external_ids") or {}

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata.get("homepage") or ""
        self.thumbnail_path: str = f"{settings.API_V1_STR}/assets/thumbnail/{self.id}"
        self.backdrop_path: str = media_metadata.get("backdrop_path") or ""
        self.poster_path: str = media_metadata.get("poster_path") or ""
        self.videos: List[Dict[str, Any]] = (
            media_metadata.get("videos", {}).get("results") or []
        )
        self.reviews: List[Dict[str, Any]] = (
            media_metadata.get("reviews", {}).get("results") or []
        )

    def append_file(self, file_metadata):
        self.id.append(file_metadata.get("id") or "")
        self.file_name.append(file_metadata.get("name") or "")
        self.path.append(file_metadata.get("path") or "")
        self.parent.append(file_metadata.get("parent") or {})
        self.modified_time.append(isoparse(
            file_metadata.get("modified_time", "1900-03-27T00:00:00.000+00:00")
        ))
        self.number_of_files += 1

    def get_logo(self, media_metadata):
        try:
            logo = (
                media_metadata.get("images", {}).get(
                    "logos", [{}])[0].get("file_path")
                or ""
            )
        except BaseException:
            logo = ""
        return logo
