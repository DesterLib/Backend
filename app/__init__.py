__license__ = "MIT"
__status__ = "Development"
__version__ = "1.0.0"
__email__ = "contact@dester.gq"
__copyright__ = "Copyright 2022, DesterLib"
__authors__ = ["Elias Benbourenane", "EverythingSuckz"]
__credits__ = ["EverythingSuckz", "Elias Benbourenane", "AlkenD"]

from logging import basicConfig, StreamHandler, getLogger, WARNING, DEBUG
from logging.handlers import TimedRotatingFileHandler
import os.path
from os import makedirs
from datetime import datetime, timezone


if not os.path.isdir("logs"):
    makedirs("logs")
if not os.path.isdir("cache"):
    makedirs("cache")

handler = TimedRotatingFileHandler("logs/dester.log", when="m", interval=60, backupCount=5)
handler.namer = lambda name: name.replace(".log", "") + ".log"

basicConfig(
    level=DEBUG,
    datefmt="%Y/%m/%d %H:%M:%S",
    format="[%(asctime)s][%(levelname)s] ==> %(message)s",
    handlers=[
        StreamHandler(),
        handler,
    ],
)
getLogger("oauth2client").setLevel(WARNING)
getLogger("googleapiclient").setLevel(WARNING)
getLogger("waitress").setLevel(WARNING)
getLogger("uvicorn").setLevel(WARNING)
getLogger("httpx").setLevel(WARNING)
logger = getLogger(__name__)
