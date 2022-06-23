from datetime import datetime
from app.settings import settings
from dateutil.parser import isoparse


class Movie:
    """Movie class"""

    __slots__: list[str] = [
        "id",
        "file_name",
        "path",
        "parent",
        "modified_time",
        "number_of_files",
        "rclone_index",
        "size",
        "subtitles",
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
        "runtime",
        "cast",
        "crew",
        "studios",
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

    def __json__(self) -> dict:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "path": self.path,
            "parent": self.parent,
            "modified_time": self.modified_time,
            "number_of_files": self.number_of_files,
            "rclone_index": self.rclone_index,
            "size": self.size,
            "subtitles": self.subtitles,
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
            "runtime": self.runtime,
            "cast": self.cast,
            "crew": self.crew,
            "studios": self.studios,
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
        self.id: list[str] = [file_metadata["id"]]
        self.file_name: list[str] = [file_metadata["name"]]
        self.path: list[str] = [file_metadata["path"]]
        self.parent: list[dict] = [file_metadata["parent"]]
        self.modified_time: list[datetime] = [isoparse(file_metadata["modified_time"])]
        self.number_of_files: int = 1
        self.rclone_index: int = rclone_index
        self.size: list[int] = [file_metadata["size"]]
        self.subtitles: list[dict] = file_metadata["subtitles"]

        # Media Info
        self.tmdb_id: int = media_metadata["id"]
        self.title: str = media_metadata["title"]
        self.original_title: str = media_metadata["original_title"]
        self.status: str = media_metadata["status"]
        self.popularity: float = media_metadata["popularity"]
        self.revenue: int = media_metadata["revenue"]
        self.rating: float = media_metadata["vote_average"]
        release_date: str = media_metadata["release_date"]
        self.release_date: datetime = datetime.strptime(release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata["tagline"]
        self.description: str = media_metadata["overview"]
        self.runtime: int = media_metadata["runtime"]
        self.cast: list[dict] = media_metadata["credits"]["cast"][:10]
        self.crew: dict = self.get_crew(media_metadata["credits"]["crew"])
        self.studios: list[dict] = media_metadata["production_companies"]
        self.genres: list[dict] = media_metadata["genres"]
        self.external_ids: dict[dict] = media_metadata["external_ids"]

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata["homepage"]
        self.thumbnail_path: str = (
            f"{settings.API_V1_STR}/assets/thumbnail/{rclone_index}/{self.id}"
        )
        self.backdrop_path: str = media_metadata["backdrop_path"]
        self.poster_path: str = media_metadata["poster_path"]
        self.videos: list[dict] = media_metadata["videos"]["results"][:10]
        self.reviews: list[dict] = media_metadata["reviews"]["results"][:10]

    def append_file(self, file_metadata):
        """Pushes a new file to the class"""
        self.id.append(file_metadata["id"])
        self.file_name.append(file_metadata["name"])
        self.path.append(file_metadata["path"])
        self.parent.append(file_metadata["parent"])
        self.modified_time.append(isoparse(file_metadata["modified_time"]))
        self.number_of_files += 1
        self.size.append(file_metadata["size"])
        self.subtitles.extend(file_metadata["subtitles"])

    def get_logo(self, media_metadata: dict) -> str:
        """Returns the movie logo URL if available"""
        try:
            logo: str = media_metadata["images"]["logos"][0]["file_path"]
        except BaseException:
            logo: str = ""
        return logo

    def get_crew(self, crew: list[dict]) -> dict:
        """Finds and curates features crew members of a movie"""
        result: dict = {
            "Creator": [],
            "Director": [],
            "Screenplay": [],
            "Screenplay by": [],
            "Author": [],
            "Writer": [],
        }
        wanted_jobs: list[str] = [
            "Creator",
            "Director",
            "Screenplay",
            "Screenplay by",
            "Author",
            "Writer",
        ]
        for member in crew:
            if member["job"] in wanted_jobs:
                result[member["job"]].append(member)
        result["Screenplay"].extend(result["Screenplay by"])
        del result["Screenplay by"]
        return result
