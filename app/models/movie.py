from datetime import datetime
from app.settings import settings
from typing import Any, Dict, List
from dateutil.parser import isoparse


class Movie:
    __slots__ = [
        "id",
        "file_name",
        "path",
        "parent",
        "modified_time",
        "number_of_files",
        "rclone_index",
        "tmdb_id",
        "title",
        "original_title",
        "status",
        "popularity",
        "revenue",
        "rating",
        "release_date",
        "year",
        "tagline",
        "description",
        "cast",
        "crew",
        "collection",
        "genres",
        "external_ids",
        "logo_path",
        "homepage",
        "thumbnail_path",
        "backdrop_path",
        "poster_path",
        "videos",
        "reviews",
    ]

    def __dict__(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "path": self.path,
            "parent": self.parent,
            "modified_time": self.modified_time,
            "number_of_files": self.number_of_files,
            "rclone_index": self.rclone_index,
            "tmdb_id": self.tmdb_id,
            "title": self.title,
            "original_title": self.original_title,
            "status": self.status,
            "popularity": self.popularity,
            "revenue": self.revenue,
            "rating": self.rating,
            "release_date": self.release_date,
            "year": self.year,
            "tagline": self.tagline,
            "description": self.description,
            "cast": self.cast,
            "crew": self.crew,
            "collection": self.collection,
            "genres": self.genres,
            "external_ids": self.external_ids,
            "logo_path": self.logo_path,
            "homepage": self.homepage,
            "thumbnail_path": self.thumbnail_path,
            "backdrop_path": self.backdrop_path,
            "poster_path": self.poster_path,
            "videos": self.videos,
            "reviews": self.reviews,
        }

    def __init__(self, file_metadata, media_metadata, rclone_index):
        # File Info
        self.id: List[str] = [file_metadata.get("id") or ""]
        self.file_name: List[str] = [file_metadata.get("name") or ""]
        self.path: List[str] = [file_metadata.get("path") or ""]
        self.parent: List[Dict[str, Any]] = [file_metadata.get("parent") or {}]
        self.modified_time: List[datetime] = [
            isoparse(
                file_metadata.get("modified_time", "1900-03-27T00:00:00.000+00:00")
            )
        ]
        self.number_of_files: int = 1
        self.rclone_index: int = rclone_index

        # Media Info
        self.tmdb_id: int = media_metadata.get("id") or 0
        self.title: str = media_metadata.get("title") or ""
        self.original_title: str = media_metadata.get("original_title") or ""
        self.status: str = media_metadata.get("status") or ""
        self.popularity: float = media_metadata.get("popularity") or 0
        self.revenue: int = media_metadata.get("revenue") or 0
        self.rating: float = media_metadata.get("vote_average") or 0
        release_date: str = media_metadata.get("release_date") or "1900-03-27"
        self.release_date: datetime = datetime.strptime(release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata.get("tagline") or ""
        self.description: str = media_metadata.get("overview") or ""
        self.cast: List[Dict[str, Any]] = (
            media_metadata.get("credits", {}).get("cast") or []
        )[:10]
        self.crew: List[Dict[str, Any]] = (
            media_metadata.get("credits", {}).get("crew") or []
        )[:10]
        self.collection: Dict[str, Any] = (
            media_metadata.get("belongs_to_collection") or {}
        )
        self.genres: List[Dict[str, Any]] = (media_metadata.get("genres") or [])[:10]
        self.external_ids: Dict[str, str] = media_metadata.get("external_ids") or {}

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata.get("homepage") or ""
        self.thumbnail_path: str = (
            f"{settings.API_V1_STR}/assets/thumbnail/{rclone_index}/{self.id}"
        )
        self.backdrop_path: str = media_metadata.get("backdrop_path") or ""
        self.poster_path: str = media_metadata.get("poster_path") or ""
        self.videos: List[Dict[str, Any]] = (
            media_metadata.get("videos", {}).get("results") or []
        )[:10]
        self.reviews: List[Dict[str, Any]] = (
            media_metadata.get("reviews", {}).get("results") or []
        )[:10]

    def append_file(self, file_metadata):
        self.id.append(file_metadata.get("id") or "")
        self.file_name.append(file_metadata.get("name") or "")
        self.path.append(file_metadata.get("path") or "")
        self.parent.append(file_metadata.get("parent") or {})
        self.modified_time.append(
            isoparse(
                file_metadata.get("modified_time", "1900-03-27T00:00:00.000+00:00")
            )
        )
        self.number_of_files += 1

    def get_logo(self, media_metadata):
        try:
            logo = (
                media_metadata.get("images", {}).get("logos", [{}])[0].get("file_path")
                or ""
            )
        except BaseException:
            logo = ""
        return logo
