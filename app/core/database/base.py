from enum import Enum


class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MONGODB = "mongodb"


class Database:
    """
    Database class to connect to the database
    This exposes all the methods to interact with the database
    """
    
    def __init__(self) -> None:
        self._database_type: DatabaseType
        
    async def connect(self) -> None:
        pass
    
    async def disconnect(self) -> None:
        pass
    