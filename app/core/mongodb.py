import certifi
from croniter import croniter
from datetime import datetime
from typing import Any, Dict, List
from pymongo import TEXT, UpdateOne, MongoClient


class MongoDB:
    def __init__(self, domain: str, username: str, password: str):
        self.domain = domain
        self.username = username
        self.password = password
        self.tlsca_ = certifi.where()
        self.client = MongoClient(
            f"mongodb+srv://{username}:{password}@{domain}/?retryWrites=true&w=majority",
            tlsCAFile=self.tlsca_,
        )
        self.db = self.client["main"]
        self.metadata = self.client["metadata"]

        self.config_col = self.db["config"]
        self.history_col = self.db["history"]
        self.movies_cache_col = self.metadata["_movies_cache"]
        self.other_col = self.db["other"]
        self.series_cache_col = self.metadata["_series_cache"]
        self.watchlist_col = self.db["watchlist"]

        self.config = {
            "app": {},
            "categories": [],
            "gdrive": {},
            "tmdb": {},
            "build": {},
            "rclone": [],
        }
        self.get_config()
        self.is_config_init = False
        self.get_is_config_init()
        self.is_metadata_init = False
        self.get_is_metadata_init()
        self.is_series_cache_init = False
        self.get_is_metadata_init()
        self.is_movies_cache_init = False
        self.get_is_movies_cache_init()
        self.is_series_cache_init = False
        self.get_is_series_cache_init()

    def get_config(self) -> Dict[str, Any]:
        config = {
            "_id": None,
            "app": {},
            "categories": [],
            "gdrive": {},
            "tmdb": {},
            "build": {},
            "rclone": [],
        }
        for document in self.config_col.find():
            config = config | document
        del config["_id"]
        self.config = config
        return config

    def get_is_config_init(self) -> bool:
        result = self.other_col.find_one({"is_config_init": {"$exists": True}}) or {
            "is_config_init": False
        }
        self.is_config_init = result["is_config_init"]
        return result["is_config_init"]

    def get_is_metadata_init(self) -> bool:
        result = self.other_col.find_one({"is_metadata_init": {"$exists": True}}) or {
            "is_metadata_init": False
        }
        self.is_metadata_init = result["is_metadata_init"]
        return result["is_metadata_init"]

    def get_is_movies_cache_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_movies_cache_init": {"$exists": True}}
        ) or {"is_movies_cache_init": False}
        self.is_movies_cache_init = result["is_movies_cache_init"]
        return result["is_movies_cache_init"]

    def get_is_series_cache_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_series_cache_init": {"$exists": True}}
        ) or {"is_series_cache_init": False}
        self.is_series_cache_init = result["is_series_cache_init"]
        return result["is_series_cache_init"]

    def get_is_build_time(self) -> bool:
        build_config = self.config_col.find_one({"build": {"$exists": True}}) or {
            "build": {"cron": "*/120 * * * *"}
        }
        last_build_time = self.other_col.find_one(
            {"last_build_time": {"$exists": True}}
        ) or {"last_build_time": datetime.fromtimestamp(1)}
        cron = croniter(
            build_config["build"].get("cron", "*/120 * * * *"), last_build_time
        )
        if datetime.now() > cron.get_next(datetime):
            return True
        else:
            return False

    def get_rclone_conf(self) -> Dict[str, Any]:
        result = self.config_col.find_one({"rclone": {"$exists": True}}) or {
            "rclone": []
        }
        rclone_conf = "\n\n".join(result["rclone"])
        self.config["rclone_conf"] = rclone_conf
        return rclone_conf

    def get_categories(self) -> List[Dict[str, Any]]:
        result = self.config_col.find_one({"categories": {"$exists": True}}) or {
            "categories": []
        }
        self.config["categories"] = result["categories"]
        return result["categories"]

    def get_tmbd_api_key(self) -> str:
        result = self.config_col.find_one({"tmdb": {"$exists": True}}) or {
            "tmdb": {"api_key": ""}
        }
        tmdb_api_key = result["tmdb"].get("api_key", "")
        self.tmdb_api_key = tmdb_api_key
        return tmdb_api_key

    def set_config(self, data: Dict[str, Any]) -> bool:
        from . import build_config

        bulk_action = []
        config_app = data.get("app", {})
        config_categories = data.get("categories", [])
        config_gdrive = data.get("gdrive", {})
        config_tmdb = data.get("tmdb", {})
        config_build = data.get("build", {})
        old_category_ids: List[Dict[str, Any]] = []
        new_category_ids: List[Dict[str, Any]] = []

        if config_app != self.config["app"]:
            bulk_action.append(self.set_app(config_app))
        if config_categories != self.config["categories"]:
            new_category_ids = sorted([x["id"] for x in config_categories])
            old_category_ids = sorted([x["id"] for x in self.config["categories"]])
            bulk_action.append(self.set_categories(config_categories))
        if config_gdrive != self.config["gdrive"]:
            bulk_action.append(self.set_gdrive(config_gdrive))
        if config_tmdb != self.config["tmdb"]:
            bulk_action.append(self.set_tmdb(config_tmdb))
        if config_build != self.config["build"]:
            bulk_action.append(self.set_build(config_build))
        if old_category_ids != new_category_ids:
            config_rclone = build_config(self.config)
            bulk_action.append(self.set_rclone(config_rclone))
            self.set_is_metadata_init(False)

        self.config_col.bulk_write(bulk_action)
        self.set_is_config_init(True)

        if self.is_metadata_init is False:
            from main import rclone_setup, metadata_setup

            rclone_setup(self.config["categories"])
            metadata_setup()

        return True

    def set_app(self, data: Dict[str, Any]):
        update_data = {
            "name": data.get("name", "Dester"),
            "title": data.get("title", "Dester"),
            "description": data.get("description", "Dester"),
            "domain": data.get("domain", ""),
        }
        update_action = UpdateOne(
            {"app": {"$exists": True}}, {"$set": {"app": update_data}}, upsert=True
        )
        self.config["app"] = update_data
        return update_action

    def set_categories(self, data: List[Dict[str, Any]]):
        update_data = []
        for item in data:
            update_data.append(
                {
                    "drive_id": item.get("drive_id"),
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "type": item.get("type", "movies"),
                    "provider": item.get("provider"),
                    "language": item.get("language", "en"),
                    "adult": item.get("adult", False),
                    "anime": item.get("anime", False),
                }
            )
        update_action = UpdateOne(
            {"categories": {"$exists": True}},
            {"$set": {"categories": update_data}},
            upsert=True,
        )
        self.config["categories"] = update_data
        return update_action

    def set_gdrive(self, data: Dict[str, Any]):
        update_data = {
            "client_id": data.get("client_id", ""),
            "client_secret": data.get("client_secret", ""),
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
        update_action = UpdateOne(
            {"gdrive": {"$exists": True}},
            {"$set": {"gdrive": update_data}},
            upsert=True,
        )
        self.config["gdrive"] = update_data
        return update_action

    def set_tmdb(self, data: Dict[str, Any]):
        update_data = {"api_key": data.get("api_key", "")}
        update_action = UpdateOne(
            {"tmdb": {"$exists": True}}, {"$set": {"tmdb": update_data}}, upsert=True
        )
        self.config["tmdb"] = update_data
        return update_action

    def set_build(self, data: Dict[str, Any]):
        update_data = {"cron": data.get("cron", "*/120 * * * *")}
        update_action = UpdateOne(
            {"build": {"$exists": True}}, {"$set": {"build": update_data}}, upsert=True
        )
        self.config["build"] = update_data
        return update_action

    def set_rclone(self, data: List[Dict[str, Any]]):
        update_data = data
        update_action = UpdateOne(
            {"rclone": {"$exists": True}},
            {"$set": {"rclone": update_data}},
            upsert=True,
        )
        self.config["rclone"] = update_data
        return update_action

    def set_is_config_init(self, is_config_init):
        if is_config_init != self.is_config_init:
            self.other_col.update_one(
                {"is_config_init": {"$exists": True}},
                {"$set": {"is_config_init": is_config_init}},
                upsert=True,
            )
            self.is_config_init = is_config_init

    def set_is_metadata_init(self, is_metadata_init):
        if is_metadata_init != self.is_metadata_init:
            self.other_col.update_one(
                {"is_metadata_init": {"$exists": True}},
                {"$set": {"is_metadata_init": is_metadata_init}},
                upsert=True,
            )
            self.is_metadata_init = is_metadata_init

    def set_is_movies_cache_init(self, is_movies_cache_init):
        if is_movies_cache_init != self.is_movies_cache_init:
            self.movies_cache_col.create_index(
                [("original_title", TEXT)], background=True, name="original_title"
            )
            self.other_col.update_one(
                {"is_movies_cache_init": {"$exists": True}},
                {"$set": {"is_movies_cache_init": is_movies_cache_init}},
                upsert=True,
            )
            self.is_metadata_init = is_movies_cache_init

    def set_is_series_cache_init(self, is_series_cache_init):
        if is_series_cache_init != self.is_series_cache_init:
            self.series_cache_col.create_index(
                [("original_title", TEXT)], background=True, name="original_title"
            )
            self.other_col.update_one(
                {"is_series_cache_init": {"$exists": True}},
                {"$set": {"is_series_cache_init": is_series_cache_init}},
                upsert=True,
            )
            self.is_series_cache_init = is_series_cache_init
