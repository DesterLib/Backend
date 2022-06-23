from app.models import Season
from datetime import datetime
from dateutil.parser import isoparse


class Serie:
    "Serie class"
    __slots__: list[str] = [
        "id",
        "file_name",
        "path",
        "parent",
        "modified_time",
        "rclone_index",
        "size",
        "tmdb_id",
        "title",
        "original_title",
        "status",
        "popularity",
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
        "total_episodes",
        "total_seasons",
        "last_episode_to_air",
        "next_episode_to_air",
        "logo_path",
        "homepage",
        "backdrop_path",
        "poster_path",
        "videos",
        "reviews",
        "seasons",
    ]

    def __json__(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "path": self.path,
            "parent": self.parent,
            "modified_time": self.modified_time,
            "rclone_index": self.rclone_index,
            "size": self.size,
            "tmdb_id": self.tmdb_id,
            "title": self.title,
            "original_title": self.original_title,
            "status": self.status,
            "popularity": self.popularity,
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
            "total_episodes": self.total_episodes,
            "total_seasons": self.total_seasons,
            "last_episode_to_air": self.last_episode_to_air,
            "next_episode_to_air": self.next_episode_to_air,
            "logo_path": self.logo_path,
            "homepage": self.homepage,
            "backdrop_path": self.backdrop_path,
            "poster_path": self.poster_path,
            "videos": self.videos,
            "reviews": self.reviews,
            "seasons": self.seasons,
        }

    def __init__(self, file_metadata, media_metadata, rclone_index):
        # File Info
        self.id: str = file_metadata["id"]
        self.file_name: str = file_metadata["name"]
        self.path: str = file_metadata["path"]
        self.parent: dict = file_metadata["parent"]
        self.modified_time: datetime = isoparse(file_metadata["modified_time"])
        self.rclone_index: int = rclone_index
        self.size: int = 0

        # Media Info
        self.tmdb_id: int = media_metadata["id"]
        self.title: str = media_metadata["name"]
        self.original_title: str = media_metadata["original_name"]
        self.status: str = media_metadata["status"]
        self.popularity: float = media_metadata["popularity"]
        self.rating: float = media_metadata["vote_average"]
        release_date: str = media_metadata["first_air_date"] or "1900-01-01"
        self.release_date: datetime = datetime.strptime(release_date, "%Y-%m-%d")
        self.year: int = self.release_date.year
        self.tagline: str = media_metadata["tagline"]
        self.description: str = media_metadata["overview"]
        runtime: str = media_metadata["episode_run_time"]
        if len(runtime) == 0:
            self.runtime = 0
        else:
            self.runtime: int = media_metadata["episode_run_time"][0]
        self.cast: list[dict] = media_metadata["credits"]["cast"][:10]
        self.crew: dict = self.get_crew(
            media_metadata["credits"]["crew"], media_metadata["created_by"]
        )
        self.studios: list[dict] = media_metadata["production_companies"]
        self.genres: list[dict] = media_metadata["genres"]
        self.external_ids: dict = media_metadata["external_ids"]
        self.total_episodes: int = media_metadata["number_of_episodes"]
        self.total_seasons: int = media_metadata["number_of_seasons"]
        self.last_episode_to_air: dict = media_metadata["last_episode_to_air"]
        self.next_episode_to_air: dict = media_metadata["next_episode_to_air"]

        # Media Resources
        self.logo_path: str = self.get_logo(media_metadata)
        self.homepage: str = media_metadata["homepage"]
        self.backdrop_path: str = media_metadata["backdrop_path"]
        self.poster_path: str = media_metadata["poster_path"]
        self.videos: list[dict] = media_metadata["videos"]["results"][:10]
        self.reviews: list[dict] = media_metadata["reviews"]["results"][:10]

        # Seasons
        seasons: list[dict] = []
        for key, season in file_metadata["seasons"].items():
            if f"season/{key}" in media_metadata:
                season_meta: Season = Season(season, media_metadata[f"season/{key}"])
                seasons.append(season_meta.__json__())
                self.size += season_meta.size
        self.seasons: list[dict] = sorted(seasons, key=lambda d: d["season_number"])
        del seasons

    def get_logo(self, media_metadata: dict) -> str:
        """Returns the series logo URL if available"""
        try:
            logo: str = media_metadata["images"]["logos"][0]["file_path"]
        except BaseException:
            logo: str = ""
        return logo

    def get_crew(self, crew: list[dict], creators: list[dict]) -> dict:
        """Finds and curates features crew members of a movie"""
        result: dict = {
            "Creator": creators,
            "Director": [],
            "Series Director": [],
            "Screenplay": [],
            "Screenplay by": [],
            "Author": [],
            "Writer": [],
            "Series Writer": [],
        }
        wanted_jobs: list[str] = [
            "Director",
            "Series Director",
            "Screenplay",
            "Screenplay by",
            "Author",
            "Writer",
            "Series Writer",
        ]
        for member in crew:
            if member["job"] in wanted_jobs:
                result[member["job"]].append(member)
        result["Screenplay"].extend(result["Screenplay by"])
        del result["Screenplay by"]
        result["Director"].extend(result["Series Director"])
        del result["Series Director"]
        result["Writer"].extend(result["Series Writer"])
        del result["Series Writer"]
        return result
