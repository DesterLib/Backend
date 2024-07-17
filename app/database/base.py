from enum import Enum
from logging import getLogger

class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MONGODB = "mongodb"

class UnimplementedMethod(Exception):
    pass

class Database:
    """
    Database class to connect to the database
    This exposes all the methods to interact with the database
    """
    
    def __init__(self) -> None:
        self._database_type: DatabaseType
        self.logger = getLogger("database")
        
    async def connect(self) -> None:
        self.logger.info(f"Using {self._database_type.value} database")
    
    async def init(self) -> None:
        raise UnimplementedMethod("init")
    
    async def disconnect(self) -> None:
        raise UnimplementedMethod("init")
    
    async def set_config(self, key: str, value: str) -> None:
        raise UnimplementedMethod("init")
    
    async def get_config(self, key: str) -> str:
        raise UnimplementedMethod("init")
    
    async def set_categories(self, id: str, name: str, folder_id: str) -> None:
        raise UnimplementedMethod("init")
    
    async def get_categories(self) -> list:
        raise UnimplementedMethod("init")
    