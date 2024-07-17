import json
from ..base import Database, DatabaseType
from pathlib import Path
from typing import Any, Optional

from tortoise import Tortoise
from .models import Config

class SQLite(Database):
    def __init__(self, db_path: Path, *args, **kwargs):
        """Implementation of the SQLite database"""
        self.db_path = db_path
        self._database_type = DatabaseType.SQLITE
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    async def connect(self):
        """Connect to the SQLite database"""    
        # self.conn = await aiosqlite.connect(self.db_path, *self.args, **self.kwargs)
        await Tortoise.init(
            db_url=f'sqlite://{self.db_path}',
            modules={'models': ['app.database.sqlite.models']}
        )
        await Tortoise.generate_schemas()
        await super().connect()

    async def init(self):
        """Initialize the SQLite database"""
        await self.connect()

    async def _close(self):
        await self.conn.close()
    
    async def disconnect(self):
        """Disconnect from the SQLite database"""
        await self._close()
    
    async def set_config(self, key: str, value: str) -> None:
        # await self._execute("INSERT OR REPLACE INTO config (name, value) VALUES (?, ?)", (key, json.dumps(value)))
        config = Config(name=key, value=json.dumps(value))
        await config.save()

    async def get_config(self, key: str, default: Any | None = None) -> str:
        config = await Config.filter(name=key).first()
        return json.loads(config.value) if config else default
    
    async def set_categories(self, id: str, name: str, folder_id: str) -> None:
        
        return 
    
    async def get_categories(self) -> list:
        return await self.get_config("categories", []) or []
    