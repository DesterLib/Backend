import json
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import certifi
from ..base import Database, DatabaseType

class MongoDatabase(Database):
    def __init__(self, domain: str, username: str, password: str, db_name: str = "dester"):
        self._domain = domain
        self._username = username
        self._password = password
        self._tlsca = certifi.where()
        self._client = AsyncIOMotorClient(
            f"mongodb+srv://{username}:{password}@{domain}/?retryWrites=true&w=majority",
            tlsCAFile=self._tlsca,
        )
        self._db = self._client[db_name]
        self._config_col = self._db["config"]
        super().__init__()

    async def connect(self) -> None:
        await self._client.admin.command("ping")
        await super().connect()

    async def find(self, collection, query={}, limit=0):
        cursor = self.db[collection].find(query).limit(limit)
        result = await cursor.to_list(length=limit)
        return result

    async def find_one(self, collection, query={}):
        result = await self.db[collection].find_one(query)
        return result

    async def insert_one(self, collection, document):
        result = await self.db[collection].insert_one(document)
        return result.inserted_id

    async def update_one(self, collection, query={}, update={}):
        result = await self.db[collection].update_one(query, {"$set": update})
        return result.modified_count

    async def delete_one(self, collection, query={}):
        result = await self.db[collection].delete_one(query)
        return result.deleted_count
    
    async def set_config(self, key: str, value: Any) -> None:
        return await self._config_col.update_one(
            {"name": key}, {"$set": {"value": json.dumps(value)}}, upsert=True
        )
    
    async def get_config(self, key: str) -> Any | None:
        value = await self._config_col.find_one({"name": key})
        return json.loads(value["value"]) if value else None
    
    async def get_categories(self) -> list:
        return await self.get_config("categories") or []