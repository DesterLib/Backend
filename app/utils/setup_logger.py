import os.path
from os import makedirs
from ..settings import settings
from logging.handlers import TimedRotatingFileHandler
from logging import INFO, DEBUG, WARNING, StreamHandler, getLogger, basicConfig, Logger


def setup_logger() -> Logger:
    """Setup the logger for the application"""
    if not os.path.isdir("logs"):
        makedirs("logs")

    handler = TimedRotatingFileHandler(
        "logs/dester.log", when="m", interval=60, backupCount=5
    )
    handler.namer = lambda name: name.replace(".log", "") + ".log"

    basicConfig(
        level=DEBUG if settings.dev else INFO,
        datefmt="%Y/%m/%d %H:%M:%S",
        format="[%(asctime)s][%(name)s][%(levelname)s] ==> %(message)s",
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
    return getLogger(__name__)