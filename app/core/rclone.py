import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from dateutil.parser import parse
from httplib2 import Http
from oauth2client.client import GoogleCredentials
from pytz import UTC


class RCloneAPI:
    def __init__(self, id):
        self.id = id
        self.fs = id + ":"
        self.RCLONE_RC_URL = "http://localhost:35530"
        self.RCLONE = {
            "mkdir": "operations/mkdir",
            "purge": "operations/purge",
            "deleteFile": "operations/deletefile",
            "createPublicLink": "operations/publiclink",
            "stats": "core/stats",
            "bwlimit": "core/bwlimit",
            "moveDir": "sync/move",
            "moveFile": "operations/movefile",
            "copyDir": "sync/copy",
            "copyFile": "operations/copyfile",
            "cleanUpRemote": "operations/cleanup",
            "noopAuth": "rc/noopauth",
            "getRcloneVersion": "core/version",
            "getRcloneMemStats": "core/memstats",
            "getOptions": "options/get",
            "getProviders": "config/providers",
            "getConfigDump": "config/dump",
            "getRunningJobs": "job/list",
            "getStatusForJob": "job/status",
            "getConfigForRemote": "config/get",
            "createConfig": "config/create",
            "updateConfig": "config/update",
            "getFsInfo": "operations/fsinfo",
            "listRemotes": "config/listremotes",
            "getFilesList": "operations/list",
            "getAbout": "operations/about",
            "deleteConfig": "config/delete",
            "stopJob": "job/stop",
            "backendCommand": "backend/command",
            "coreCommand": "core/command",
            "transferred": "core/transferred",
            "getSize": "operations/size",
            "statsDelete": "core/stats-delete",
            "statsReset": "core/stats-reset",
        }
        self.fs_conf = self.rc_conf()
        self.fs_conf["token"] = json.loads(self.fs_conf["token"])

    def rc_ls(self, options: Optional[dict] = {}) -> List[Dict[str, Any]]:
        rc_data = {
            "fs": self.fs,
            "remote": "",
            "opt": options,
        }
        result = requests.post(
            "%s/%s" % (self.RCLONE_RC_URL, self.RCLONE["getFilesList"]),
            data=json.dumps(rc_data),
            headers={"Content-Type": "application/json"},
        ).json()
        return result["list"]

    def rc_conf(self) -> Dict:
        rc_data = {"name": self.id}
        result = requests.post(
            "%s/%s" % (self.RCLONE_RC_URL, self.RCLONE["getConfigForRemote"]),
            data=json.dumps(rc_data),
            headers={"Content-Type": "application/json"},
        ).json()
        return result

    def fetch_movies(self) -> List[Dict[str, Any]]:
        rc_ls_result = self.rc_ls({"recurse": True, "filesOnly": False})
        metadata = []
        dirs = {}
        for item in rc_ls_result:
            if item["IsDir"] == False and "video" in item["MimeType"]:
                parent_path = item["Path"].replace("/" + item["Name"], "")
                parent = dirs[parent_path]
                metadata.append(
                    {
                        "id": item["ID"],
                        "name": item["Name"],
                        "path": item["Path"],
                        "type": "file",
                        "parent": parent,
                        "mimeType": item["MimeType"],
                        "modifiedTime": item["ModTime"],
                        "videoMediaMetadata": {},
                        "hasThumbnail": False,
                        "subtitles": None,
                    }
                )
            elif item["IsDir"] == True:
                dirs[item["Path"]] = {
                    "id": item["ID"],
                    "name": item["Name"],
                    "path": item["Path"],
                }
            elif item["IsDir"] == False and item["Name"].endswith((".srt", ".vtt")):
                # Subtitle management
                pass
        return metadata

    def fetch_series(self) -> List[Dict[str, Any]]:
        rc_ls_result = self.rc_ls({"recurse": True, "maxDepth": 2})
        metadata = []
        parent_dirs = {
            "": {
                "path": "",
                "depth": 0,
                "json_path": "",
            }
        }
        for item in rc_ls_result:
            if len(item["Path"].split("/")) == 1:
                parent_path = ""
            else:
                parent_path = item["Path"].replace("/" + item["Name"], "")
            parent = parent_dirs[parent_path]
            if item["IsDir"] == False:
                if parent["depth"] == 2:
                    season_metadata = eval("metadata" + parent["json_path"])
                    season_metadata["episodes"].append(
                        {
                            "id": item["ID"],
                            "name": item["Name"],
                            "path": item["Path"],
                            "parent": parent,
                            "modified_time": item["ModTime"],
                        }
                    )
            else:
                parent_dirs[item["Path"]] = {
                    "id": item["ID"],
                    "name": item["Name"],
                    "path": item["Path"],
                    "depth": parent["depth"] + 1,
                }
                if parent["depth"] == 0:
                    metadata.append(
                        {
                            "id": item["ID"],
                            "name": item["Name"],
                            "path": item["Path"],
                            "parent": parent,
                            "modified_time": item["ModTime"],
                            "seasons": {},
                            "json_path": "[%s]" % str(len(metadata)),
                        }
                    )
                    parent_dirs[item["Path"]]["json_path"] = "[%s]" % str(
                        len(metadata) - 1
                    )
                elif parent["depth"] == 1:
                    series_metadata = eval("metadata" + parent["json_path"])
                    season = re.search(
                        r"^s(?:\w+)? ?\-?\.?(\d{0,3})$", item["Name"], flags=2
                    )
                    season = season.group(1) if season else "1"
                    if season != "0":
                        season = season.lstrip("0")
                    series_metadata["seasons"][season] = {
                        "id": item["ID"],
                        "name": item["Name"],
                        "path": item["Path"],
                        "parent": parent,
                        "modified_time": item["ModTime"],
                        "episodes": [],
                        "json_path": parent["json_path"] + '["%s"]' % season,
                    }
                    parent_dirs[item["Path"]]["json_path"] = (
                        parent["json_path"] + '["seasons"]["%s"]' % season
                    )
        return metadata

    def refresh(self) -> Dict:
        creds = GoogleCredentials(
            client_id=self.fs_conf["client_id"],
            client_secret=self.fs_conf["client_secret"],
            access_token=self.fs_conf["token"]["access_token"],
            refresh_token=self.fs_conf["token"]["refresh_token"],
            token_uri="https://accounts.google.com/o/oauth2/token",
            token_expiry=None,
            user_agent=None,
        )
        creds.refresh(creds.authorize(Http()))
        result = {
            "access_token": creds.access_token,
            "token_type": "Bearer",
            "refresh_token": creds.refresh_token,
            "expiry": creds.token_expiry,
        }
        return result

    def thumbnail(self, id) -> Union[str, None]:
        if parse(self.fs_conf["token"]["expiry"]) <= UTC.localize(datetime.now()):
            self.fs_conf["token"] = self.refresh()
        result = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{id}?supportsAllDrives=true&fields=thumbnailLink",
            headers={
                "Authorization": "Bearer %s" % self.fs_conf["token"]["access_token"]
            },
        ).json()
        if thumb := result.get("thumbnailLink"):
            return re.sub(r"=s\d+$", "", thumb)
