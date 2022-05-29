__all__ = ["main_router"]

import os.path
import pkgutil
from .. import logger
from fastapi import APIRouter


func = "router"
module = "app.api.routes.{}"
main_router = APIRouter()
pkgpath = os.path.join(os.path.dirname(__file__), "routes")


for _, mod, _ in pkgutil.iter_modules([pkgpath]):
    try:
        imported_route = getattr(__import__(module.format(mod), fromlist=[func]), func)
    except AttributeError:
        logger.warning(f"{module.format(mod)} does not have a {func} function")
        logger.warning(f"Skipping {module.format(mod)}")
        continue
    except Exception as e:
        raise e
    main_router.include_router(imported_route)
    logger.debug(f"route {mod} was added")
