import json
import re
from typing import Any, Dict, List, Optional

import requests

RCLONE_RC_URL = "http://localhost:35530"
RCLONE = {
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


def rc_ls(fs: str, options: Optional[dict] = {}) -> List[Dict[str, Any]]:
    rc_data = {
        "fs": fs,
        "remote": "",
        "opt": options,
    }
    result = requests.post(
        "%s/%s" % (RCLONE_RC_URL, RCLONE["getFilesList"]),
        data=json.dumps(rc_data),
        headers={"Content-Type": "application/json"},
    ).json()
    return result["list"]


def fetch_movies(fs: str) -> List[Dict[str, Any]]:
    rc_ls_result = rc_ls(fs, {"recurse": True, "filesOnly": False})
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
        elif item["isDir"] == True:
            dirs[item["Path"]] = {
                "id": item["ID"],
                "name": item["Name"],
                "path": item["Path"],
            }
        elif item["IsDir"] == False and item["Name"].endswith((".srt", ".vtt")):
            # Subtitle management
            pass
    return metadata


def fetch_series(fs: str) -> List[Dict[str, Any]]:
    rc_ls_result = rc_ls(fs, {"recurse": True, "maxDepth": 2})
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
                parent_dirs[item["Path"]]["json_path"] = "[%s]" % str(len(metadata) - 1)
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
