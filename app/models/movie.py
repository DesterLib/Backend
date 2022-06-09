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
        self.id: list = [file_metadata["id"]]
        self.file_name: list = [file_metadata["name"]]
        self.path: list = [file_metadata["path"]]
        self.parent: list = [file_metadata["parent"]]
        self.modified_time: list = [isoparse(file_metadata["modified_time"])]
        self.number_of_files: int = 1
        self.rclone_index: int = rclone_index

        # Media Info
        self.tmdb_id: int = media_metadata["id"]
        self.title: str = media_metadata["title"]
        self.original_title: str = media_metadata["original_title"]
        self.status: str = media_metadata["status"]
        self.popularity: float = media_metadata["popularity"]
        self.revenue: int = media_metadata["revenue"]
        self.rating: float = media_metadata["vote_average"]
        release_date: str = media_metadata["release_date"]
        self.release_date: datetime = datetime.strptime(
            release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata["tagline"]
        self.description: str = media_metadata["overview"]
        self.cast: list = media_metadata["credits"]["cast"][:10]
        self.crew: list = self.get_crew(media_metadata["credits"]["crew"])
        self.genres: list = media_metadata["genres"]
        self.external_ids: dict = media_metadata["external_ids"]

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata["homepage"]
        self.thumbnail_path: str = f"{settings.API_V1_STR}/assets/thumbnail/{rclone_index}/{self.id}"
        self.backdrop_path: str = media_metadata["backdrop_path"]
        self.poster_path: str = media_metadata["poster_path"]
        self.videos: list = media_metadata["videos"]["results"][:10]
        self.reviews: list = media_metadata["reviews"]["results"][:10]

    def append_file(self, file_metadata):
        self.id.append(file_metadata["id"])
        self.file_name.append(file_metadata["name"])
        self.path.append(file_metadata["path"])
        self.parent.append(file_metadata["parent"])
        self.modified_time.append(isoparse(file_metadata["modified_time"]))
        self.number_of_files += 1

    def get_logo(self, media_metadata: dict) -> str:
        try:
            logo: str = (
                media_metadata["images"]["logos"][0]["file_path"]
            )
        except BaseException:
            logo: str = ""
        return logo

    def get_crew(self, crew: list) -> list:
        result: list = []
        for member in crew:
            if member["job"] == "Director":
                result.append(member)
            elif member["job"] == "Screenplay":
                result.append(member)
        return result
