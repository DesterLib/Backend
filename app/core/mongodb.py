from datetime import datetime
from typing import Any, Dict, List

from croniter import croniter
from pymongo import MongoClient
import pymongo


class MongoDB:
    def __init__(self, domain: str, username: str, password: str):
        self.domain = domain
        self.username = username
        self.password = password
        self.client = MongoClient(
            f"mongodb+srv://{username}:{password}@{domain}/?retryWrites=true&w=majority")
        self.db = self.client["main"]
        self.metadata = self.client["metadata"]

        self.config_col = self.db["config"]
        self.history_col = self.db["history"]
        self.movies_cache_col = self.db["movies_cache"]
        self.other_col = self.db["other"]
        self.series_cache_col = self.db["series_cache"]
        self.watchlist_col = self.db["watchlist"]

        self.config = {}
        self.get_config()
        self.is_config_init = False
        self.get_is_config_init()
        self.is_metadata_init = False
        self.get_is_metadata_init()
        self.rclone_conf = self.config.get("rclone_conf", "")
        self.categories = self.config.get("categories", [])

    def get_config(self) -> Dict[str, Any]:
        config = {"_id": None}
        for document in self.config_col.find():
            config = config | document
        del config["_id"]
        self.config = config
        return config

    def get_is_config_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_config_init": {"$type": "bool"}}) or {"is_config_init": False}
        self.is_config_init = result["is_config_init"]
        return result["is_config_init"]

    def get_is_metadata_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_metadata_init": {"$type": "bool"}}) or {"is_metadata_init": False}
        self.is_metadata_init = result["is_metadata_init"]
        return result["is_metadata_init"]

    def get_is_build_time(self) -> bool:
        build_config = self.config_col.find_one(
            {"build": {"$type": "object"}}) or {"build": {"cron": "*/120 * * * *"}}
        last_build_time = self.other_col.find_one(
            {"last_build_time": {"$type": "date"}}) or {"last_build_time": datetime.fromtimestamp(1)}
        cron = croniter(build_config["build"].get(
            "cron", "*/120 * * * *"), last_build_time)
        if datetime.now() > cron.get_next(datetime):
            return True
        else:
            return False

    def get_rclone_conf(self) -> Dict[str, Any]:
        result = self.config_col.find_one(
            {"rclone": {"$type": "array"}}) or {"rclone": []}
        rclone_conf = "\n\n".join(result["rclone"])
        self.rclone_conf = rclone_conf
        return rclone_conf

    def get_categories(self) -> List[Dict[str, Any]]:
        result = self.config_col.find_one(
            {"categories": {"$type": "array"}}) or {"categories": []}
        self.categories = result["categories"]
        return result["categories"]

    def get_tmbd_api_key(self) -> str:
        result = self.config_col.find_one(
            {"tmdb": {"$type": "object"}}) or {"tmdb": {"api_key": ""}}
        tmdb_api_key = result["tmdb"].get("api_key", "")
        self.tmdb_api_key = tmdb_api_key
        return tmdb_api_key

    def set_config(self, data: Dict[str, Any]) -> bool:
        from . import build_config
        bulk_action = []
        for k, v in data.items():
            bulk_action.append(pymongo.InsertOne({k: v}))
        rclone_conf = build_config(data)
        bulk_action.append(pymongo.InsertOne({"rclone": rclone_conf}))
        self.config_col.delete_many({})
        self.config_col.bulk_write(bulk_action)
        self.set_is_config_init(True)
        return True

    def set_is_config_init(self, is_config_init):
        self.other_col.update_one({"is_config_init": {"$type": "bool"}}, {
                                  "$set": {"is_config_init": is_config_init}}, upsert=True)
        self.is_config_init = is_config_init

    def set_is_metadata_init(self, is_metadata_init):
        self.other_col.update_one({"is_metadata_init": {"$type": "bool"}}, {
                                  "$set": {"is_metadata_init": is_metadata_init}}, upsert=True)
        self.is_metadata_init = is_metadata_init
