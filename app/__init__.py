import logging
import os
import os.path
from datetime import datetime

__author__ = "wrench"

if not os.path.isdir("logs"):
    os.makedirs("logs")
if not os.path.isdir("cache"):
    os.makedirs("cache")

logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y/%m/%d %H:%M:%S",
    format="[%(asctime)s][%(levelname)s] ==> %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "logs/{}.log".format(datetime.now().strftime("%Y-%m-%d_%H%M%S")), mode="w"
        ),
    ],
)
logging.getLogger("oauth2client").setLevel(logging.WARNING)
logging.getLogger("googleapiclient").setLevel(logging.WARNING)
logging.getLogger("waitress").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
