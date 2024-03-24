import aiosqlite
from .base import Database, DatabaseType
from pathlib import Path


class SQLite(Database):
    def __init__(self, db_path: Path, *args, **kwargs):
        """Implementation of the SQLite database"""
        self.db_path = db_path
        self.conn: aiosqlite.Connection = None
        self._database_type = DatabaseType.SQLITE
        self.args = args
        self.kwargs = kwargs

    async def connect(self):
        """Connect to the SQLite database"""
        self.conn = await aiosqlite.connect(self.db_name, *self.args, **self.kwargs)

    async def _execute(self, query: str, parameters=None):
        if parameters is None:
            parameters = []
        cursor = await self.conn.cursor()
        await cursor.execute(query, parameters)
        await self.conn.commit()

    async def _fetch(self, query, parameters=None):
        if parameters is None:
            parameters = []
        cursor = await self.conn.cursor()
        await cursor.execute(query, parameters)
        return await cursor.fetchall()

    async def _close(self):
        await self.conn.close()
    
    async def disconnect(self):
        """Disconnect from the SQLite database"""
        await self._close()
        