import requests
import regex as re
import ujson as json
from os import path
from httplib2 import Http
from app.settings import settings
from oauth2client.client import GoogleCredentials


def build_config(config) -> list:
    """Generates an rclone config"""
    rclone_conf: list = []
    for category in config["categories"]:
        provider = category.get("provider", "gdrive")
        if provider == "gdrive":
            provider = "drive"
            client_id = config["gdrive"]["client_id"]
            client_secret = config["gdrive"]["client_secret"]
            token = json.dumps(
                {
                    "access_token": config["gdrive"]["access_token"],
                    "token_type": "Bearer",
                    "refresh_token": config["gdrive"]["refresh_token"],
                    "expiry": "2022-03-27T00:00:00.000+00:00",
                },
            )
            id = category["id"]
            safe_fs = "".join(c for c in id if c.isalnum())
            drive_id = category["drive_id"]
            rclone_conf.append(
                f"[{safe_fs}]\ntype = drive\nclient_id = {client_id}\nclient_secret = {client_secret}\nscope = drive\nroot_folder_id = {id}\ntoken = {token}\nteam_drive = {drive_id}\n"
            )
        elif provider == "onedrive":
            token = json.dumps(
                {
                    "access_token": config["onedrive"]["access_token"],
                    "token_type": "Bearer",
                    "refresh_token": config["onedrive"]["refresh_token"],
                    "expiry": "2022-03-27T00:00:00.000+00:00",
                },
            )
            id = category["id"]
            safe_fs = "".join(c for c in id if c.isalnum())
            drive_id = category["drive_id"]
            rclone_conf.append(
                f"[{safe_fs}]\ntype = onedrive\nscope = drive\nroot_folder_id = {id}\ntoken = {token}\ndrive_id = {drive_id}\ndrive_type = personal"
            )
        elif provider == "sharepoint":
            token = json.dumps(
                {
                    "access_token": config["sharepoint"]["access_token"],
                    "token_type": "Bearer",
                    "refresh_token": config["sharepoint"]["refresh_token"],
                    "expiry": "2022-03-27T00:00:00.000+00:00",
                },
            )
            id = category.get("id")
            drive_id = category.get("drive_id")
            if id is not None and drive_id is not None:
                safe_fs = "".join(c for c in id if c.isalnum())
                rclone_conf.append(
                    f"[{safe_fs}]\ntype = onedrive\nroot_folder_id = {id}\ntoken = {token}\ndrive_id = {drive_id}\ndrive_type = documentLibrary"
                )
            elif drive_id is not None:
                safe_fs = "".join(c for c in drive_id if c.isalnum())
                rclone_conf.append(
                    f"[{safe_fs}]\ntype = onedrive\ntoken = {token}\ndrive_id = {drive_id}\ndrive_type = documentLibrary"
                )
    return rclone_conf


class RCloneAPI:
    def __init__(self, data: dict, index: int):
        self.data: dict = data
        self.index: int = index
        self.id: str = data.get("id") or data.get("drive_id") or ""
        self.fs: str = "".join(c for c in self.id if c.isalnum()) + ":"
        self.provider: str = data.get("provider") or "gdrive"
        self.RCLONE_RC_URL: str = "http://localhost:35530"
        self.RCLONE: dict = {
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
            "getFileInfo": "operations/stat",
            "statsDelete": "core/stats-delete",
            "statsReset": "core/stats-reset",
        }
        self.fs_conf: dict = self.rc_conf()
        self.refresh()

    def rc_ls(self, options: dict = {}) -> list:
        """Returns a recursive list of files"""
        rc_data: dict = {
            "fs": self.fs,
            "remote": "",
            "opt": options,
        }
        result = requests.post(
            self.RCLONE_RC_URL + "/" + self.RCLONE["getFilesList"],
            data=json.dumps(rc_data),
            headers={"Content-Type": "application/json"},
        ).json()
        return result["list"]

    def rc_conf(self) -> dict:
        """Retrieves the Rclone config of the current remote"""
        rc_data: dict = {"name": self.fs[:-1]}
        result = requests.post(
            self.RCLONE_RC_URL + "/" + self.RCLONE["getConfigForRemote"],
            data=json.dumps(rc_data),
            headers={"Content-Type": "application/json"},
        ).json()
        result["token"] = json.loads(result.get("token", "{}"))
        return result

    def fetch_movies(self) -> list:
        """Returns movie files"""
        rc_ls_result = self.rc_ls({"recurse": True, "filesOnly": False})
        metadata: list = []
        dirs: dict = {}
        file_names: dict = {}
        sub_index: int = 0
        for item in rc_ls_result:
            if item["IsDir"] is False and (
                "video" in item["MimeType"]
                or item["Name"]
                .lower()
                .endswith((".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"))
            ):
                parent_path = item["Path"].replace("/" + item["Name"], "")
                parent = dirs.get(parent_path)
                curr_metadata = {
                    "id": item["ID"],
                    "name": item["Name"],
                    "path": item["Path"],
                    "parent": parent,
                    "mime_type": item["MimeType"],
                    "size": item["Size"],
                    "subtitles": [],
                    "modified_time": item["ModTime"],
                }
                path_without_extention = path.splitext(item["Path"])[0]
                file_name = file_names.get(path_without_extention)
                if file_name:
                    curr_metadata["subtitles"] = file_name["subtitles"]
                    file_names[path_without_extention]["found"] = True
                    file_names[path_without_extention]["index"] = sub_index
                else:
                    file_names[path_without_extention] = {
                        "found": True,
                        "index": sub_index,
                        "subtitles": [],
                    }
                metadata.append(curr_metadata)
                sub_index += 1
            elif item["IsDir"] is True:
                dirs[item["Path"]] = {
                    "id": item["ID"],
                    "name": item["Name"],
                    "path": item["Path"],
                }
            elif item["IsDir"] is False and item["Name"].endswith(
                (".vtt", ".srt", ".ass", ".ssa")
            ):
                path_without_extention = path.splitext(item["Path"])[0]
                if path_without_extention[-3] == ".":
                    path_without_extention = path_without_extention[:-3]
                elif path_without_extention[-4] == ".":
                    path_without_extention = path_without_extention[:-4]
                sub_metadata = {
                    "id": item["ID"],
                    "name": item["Name"],
                    "path": item["Path"],
                }
                file_name = file_names.get(path_without_extention)
                if file_name:
                    if file_name["found"] is True:
                        metadata[file_name["index"]]["subtitles"].append(sub_metadata)
                    else:
                        file_names[path_without_extention]["subtitles"].append(
                            sub_metadata
                        )
                else:
                    file_names[path_without_extention] = {
                        "found": False,
                        "index": None,
                        "subtitles": [sub_metadata],
                    }

        return metadata

    def fetch_series(self) -> list:
        """Returns series files"""
        rc_ls_result = self.rc_ls({"recurse": True, "maxDepth": 2})
        metadata: list = []
        parent_dirs: dict = {
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
            if item["IsDir"] is False:
                if parent["depth"] == 2:
                    season_metadata = eval("metadata" + parent["json_path"])
                    season_metadata["episodes"].append(
                        {
                            "id": item["ID"],
                            "name": item["Name"],
                            "path": item["Path"],
                            "parent": parent,
                            "mime_type": item["MimeType"],
                            "size": item["Size"],
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
                            "mime_type": item["MimeType"],
                            "modified_time": item["ModTime"],
                            "seasons": {},
                            "json_path": f"[{len(metadata)}]",
                        }
                    )
                    parent_dirs[item["Path"]]["json_path"] = f"[{len(metadata) - 1}]"
                elif parent["depth"] == 1:
                    series_metadata = eval("metadata" + parent["json_path"])
                    season = re.search(
                        r"(?<=Season.|season.|S|s)\d{1,3}|^\d{1,3}$", item["Name"]
                    )
                    season = season.group() if season else "1"
                    if season != "0":
                        season = season.lstrip("0")
                    series_metadata["seasons"][season] = {
                        "id": item["ID"],
                        "name": item["Name"],
                        "path": item["Path"],
                        "parent": parent,
                        "mime_type": item["MimeType"],
                        "modified_time": item["ModTime"],
                        "episodes": [],
                        "json_path": parent["json_path"] + f'["{season}"]',
                    }
                    parent_dirs[item["Path"]]["json_path"] = (
                        parent["json_path"] + f'["seasons"]["{season}"]'
                    )
        return metadata

    def refresh(self) -> dict:
        "Refreshes Google Drive credentials"
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
        self.fs_conf["token"] = result
        return result

    def size(self, path: str) -> int:
        """Retrieves the size of a folder or file"""
        options = {
            "no-modtime": True,
            "no-mimetype": True,
        }
        rc_data: dict = {
            "fs": self.fs,
            "remote": path,
            "opt": options,
        }
        result = requests.post(
            "%s/%s" % (self.RCLONE_RC_URL, self.RCLONE["getFileInfo"]),
            data=json.dumps(rc_data),
            headers={"Content-Type": "application/json"},
        ).json()
        return result["item"]["Size"]

    def stream(self, path: str):
        """Generates the stream URL for a file"""
        stream_url = (
            f"http://localhost:{settings.RCLONE_LISTEN_PORT}/[{self.fs}]/{path}"
        )
        return stream_url

    def thumbnail(self, id) -> str:
        """Returns a thumbnail for a video file"""
        return ""
