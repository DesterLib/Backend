__license__ = "MIT"
__status__ = "Development"
__version__ = "1.0.0-beta"
__email__ = "contact@dester.gq"
__copyright__ = "Copyright 2022, Dester"
__authors__ = ["Elias Benbourenane", "EverythingSuckz"]
__credits__ = ["EverythingSuckz", "Elias Benbourenane", "AlkenD"]

from pathlib import Path
from app.utils.setup_logger import setup_logger

from app.database.mongo.mongo_con import MongoDatabase
from app.database.sqlite.sqlite_con import SQLite
from .settings import settings

logger = setup_logger()
    
if settings.mongo_dns:
    logger.info("Connecting to MongoDB...")
    db = MongoDatabase()
else:
    logger.info("Using sqlite database")
    _database_path = Path("database.db")
    db = SQLite(_database_path)

