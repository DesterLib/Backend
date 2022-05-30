from datetime import datetime
from typing import Any, Dict, List

from croniter import croniter
from pymongo import MongoClient


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

    def get_is_config_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_config_init": {"$type": "bool"}}) or {"is_config_init": False}
        return result["is_config_init"]

    def get_is_metadata_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_config_init": {"$type": "bool"}}) or {"is_config_init": False}
        return result["is_config_init"]

    def get_is_metadata_init(self) -> bool:
        result = self.other_col.find_one(
            {"is_metadata_init": {"$type": "bool"}}) or {"is_metadata_init": False}
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
        return rclone_conf

    def get_categories(self) -> List[Dict[str, Any]]:
        result = self.config_col.find_one(
            {"categories": {"$type": "array"}}) or {"categories": []}
        return result["categories"]

    def get_tmbd_api_key(self) -> str:
        result = self.config_col.find_one(
            {"tmdb": {"$type": "object"}}) or {"tmdb": {"api_key": ""}}
        return result["tmdb"].get("api_key", "")

    def set_is_config_init(self, is_config_init):
        self.other_col.update_one({"is_config_init": {"$type": "bool"}}, {
                                  "$set": {"is_config_init": is_config_init}}, upsert=True)

    def set_is_metadata_init(self, is_metadata_init):
        self.other_col.update_one({"is_metadata_init": {"$type": "bool"}}, {
                                  "$set": {"is_metadata_init": is_metadata_init}}, upsert=True)
