__license__ = "MIT"
__status__ = "Development"
__version__ = "1.0.0"
__email__ = "contact@dester.gq"
__copyright__ = "Copyright 2022, DesterLib"
__authors__ = ["Elias Benbourenane", "EverythingSuckz"]
__credits__ = ["EverythingSuckz", "Elias Benbourenane", "AlkenD"]

import logging
import os.path
from datetime import datetime, timezone
from os import makedirs

if not os.path.isdir("logs"):
    makedirs("logs")
if not os.path.isdir("cache"):
    makedirs("cache")

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y/%m/%d %H:%M:%S",
    format="[%(asctime)s][%(levelname)s] ==> %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "logs/{}.log".format(datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")), mode="w"
        ),
    ],
)
logging.getLogger("oauth2client").setLevel(logging.WARNING)
logging.getLogger("googleapiclient").setLevel(logging.WARNING)
logging.getLogger("waitress").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
