from app.settings import settings
from app.core.mongodb import MongoDB
from app.core.rclone import RCloneAPI


mongo = MongoDB(
    settings.MONGODB_DOMAIN, settings.MONGODB_USERNAME, settings.MONGODB_PASSWORD
)
rclone: dict[int, RCloneAPI] = {}
