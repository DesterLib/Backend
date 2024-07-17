from typing import Dict
from app.settings import settings
from app.core.rclone import RCRemote

rclone: Dict[int, RCRemote] = {}