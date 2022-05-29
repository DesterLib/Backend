from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase, AgnosticCollection


class MongoDB:
    def __init__(self, uri: str, database_name: str):
        self._client = AsyncIOMotorClient(uri)
        self.db: AgnosticDatabase = self._client[database_name]

        self.user_col: AgnosticCollection = self.db["USERS"]
        self.wl_col: AgnosticCollection = self.db["WATCHLIST"]
        self.temp_col: AgnosticCollection = self.db["TEMP"]
