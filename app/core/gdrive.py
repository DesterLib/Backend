import re
import httplib2
from .. import logger
import random
from itertools import groupby
from googleapiclient.errors import HttpError
from oauth2client.client import GoogleCredentials
from typing import Any, Dict, List, Optional, Union
from googleapiclient.discovery import build, Resource
from oauth2client.service_account import ServiceAccountCredentials
from app.settings import settings
class GdriveNotInitialized(Exception):
    pass

class DriveAPI:
    def __init__(self,
                 account_credentials: Optional[Union[GoogleCredentials, Dict[str, Any]]] = None,
                 service_account_credentials: Optional[Union[ServiceAccountCredentials, Dict[str, Any]]] = None
                ) -> None:
        
        self.fully_initialized = False
        self.token_uri = "https://accounts.google.com/o/oauth2/token"
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        
        if not isinstance(account_credentials, Optional[GoogleCredentials]):
            account_credentials = GoogleCredentials(client_id=account_credentials['gdrive_client_id'],
                                                    access_token=account_credentials['gdrive_access_token'],
                                                    client_secret=account_credentials['gdrive_client_secret'],
                                                    refresh_token=account_credentials['gdrive_refresh_token'],
                                                    token_uri=self.token_uri, token_expiry=None, user_agent=None)
        if not isinstance(service_account_credentials, Optional[ServiceAccountCredentials]):
            service_account_credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=service_account_credentials, 
                                                                                           token_uri=self.token_uri,
                                                                                           scopes=self.scopes)
        
        self.account_credentials = account_credentials
        self.service_account_credentials = service_account_credentials

        self.credentials = account_credentials or service_account_credentials
        self.drive_service = None
        if self.credentials:
            self.fully_initialized = True
            self.refresh()
        else:
            print("Dummy gdrive class initialized")
    
    
    @classmethod
    def from_sa_json(cls, json: Dict[str, Any]) -> 'DriveAPI':
        return cls(
            account_credentials=None,
            service_account_credentials=json,
        )
    
    @classmethod
    def from_gac_json(cls, json: Dict[str, Any]) -> 'DriveAPI':
        return cls(
            account_credentials=json,
            service_account_credentials=None,
        )
    

    def refresh(self) -> None:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        http = self.credentials.authorize(httplib2.Http())
        self.credentials.refresh(http)
    
    @property
    def files(self) -> Optional["Resource"]:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        if not self.drive_service:
            self.drive_service = build("drive", "v3", credentials=self.credentials)
        return self.drive_service.files()
    
    def get_thumbnail_url(self, file_id: str) -> Optional[Dict[str, Any]]:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        response = self.files.get(
            supportsAllDrives = True,
            fields = "thumbnailLink",
            fileId = file_id,
        ).execute()
        if thumb := response.get("thumbnailLink"):
            return re.sub(r"=s\d+$", "", thumb)
    
    def get_files(self, folder_id):
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        page_token = None
        while True:
            response = self.files.list(
                pageToken = page_token,
                supportsAllDrives = True,
                pageSize = 200,
                includeItemsFromAllDrives = True,
                fields = "files(\
                    id,\
                    name,\
                    parents,\
                    mimeType,\
                    modifiedTime,\
                    hasThumbnail,\
                    shortcutDetails,\
                    videoMediaMetadata \
                ), incompleteSearch, nextPageToken",
                q = f"'{folder_id}' in parents \
                    and trashed = false \
                    and (\
                        mimeType = 'text/plain' \
                        or mimeType contains 'video' \
                        or mimeType = 'application/octet-stream'\
                        or mimeType = 'application/vnd.google-apps.folder' \
                        or mimeType = 'application/vnd.google-apps.shortcut' \
                    )",
                orderBy = "name",    
            ).execute()
            for file in response["files"]:
                if file["mimeType"] == "application/vnd.google-apps.folder":
                    file["type"] = "directory"
                elif file["mimeType"] == "application/vnd.google-apps.shortcut":
                    tmp_file = {
                        "id": file["shortcutDetails"]["targetId"],
                        "name": file["name"],
                        "mimeType": file["shortcutDetails"]["targetMimeType"],
                        "parents": file["parents"],
                        "modifiedTime": file.get("modifiedTime"),
                        "videoMediaMetadata": file.get("videoMediaMetadata"),
                        "hasThumbnail": file.get("hasThumbnail"),
                        
                    }
                    if tmp_file["mimeType"] == "application/vnd.google-apps.folder":
                        tmp_file["type"] = "directory"
                        file = tmp_file
                    else:
                        tmp_file["type"] = "file"
                        file = tmp_file
                else:
                    file["type"] = "file"
                yield file
            page_token = response.get('nextPageToken')
            if page_token is None:
                return
            
    def dig_folders(self, folder_id: str, data:  Optional[List[Dict[str, Any]]] = []) -> None:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        for file in self.get_files(folder_id):
            print(f"Digged '{file.get('name')}'")
            if file["mimeType"] == "application/vnd.google-apps.folder":
                self.dig_folders(file["id"], data)
            else:
                data.append(file)

    def fetch_movies(self, folder_id: str) -> List[Dict[str, Any]]:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        data = []
        raw_data = []
        self.dig_folders(folder_id, raw_data)
        for block in list(
                    filter(
                        lambda x:
                            any(d.get('name', "")
                                .endswith(ext)
                                for ext in
                                    [".mkv", ".mp4"]
                                for d in x
                            ) and not
                            any(d.get('name', "").endswith(".txt")
                                for d in x
                            ),
                        [
                        [val for val in raw_data if
                        val["parents"][0] == k]
                        for k, _ in groupby(raw_data,
                                lambda x: x["parents"][0])])):
            metadata = {}
            subs = []
            for file in block:
                if "video" in file.get("mimeType", "").lower():
                    metadata["id"] = file["id"]
                    metadata["name"] = file["name"]
                    metadata["parent"] = file["parents"][0]
                    metadata["modifiedTime"] = file["modifiedTime"]
                    metadata["videoMediaMetadata"] = file.get("videoMediaMetadata")
                    metadata["hasThumbnail"] = file.get("hasThumbnail")
                elif file.get("name", "").endswith(".srt") and file.get("parents", [])[0] != folder_id:
                    file = dict(
                        id=file["id"],
                        name=file["name"],
                    )
                    subs.append(file)
            metadata["subtitles"] = subs or None
            data.append(metadata)
        return data
    
    def fetch_series(self, folder_id: str) -> List[Dict[str, Any]]:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        dirs = self.get_files(folder_id)
        data = []
        for dir in dirs:
            print(f"Digging into '{dir.get('name')}'")
            # Loki
            metadata = {}
            # check if 'Loki' is a folder
            if dir.get("mimeType", "").lower() == "application/vnd.google-apps.folder":
                metadata["id"] = dir["id"]
                metadata["name"] = dir["name"]
                metadata["seasons"] = {}
                for file in self.get_files(folder_id=dir["id"]):
                    # Loki S1
                    if "video" in file.get("mimeType", "").lower():
                        if not metadata["seasons"].get("1"):
                            metadata["seasons"] = {"1": dict(episodes=[])}
                        metadata["seasons"]["1"]["episodes"].append(dict(
                            id=file["id"],
                            name=file["name"],
                            modified_time=file["modifiedTime"],
                            video_metadata=file.get("videoMediaMetadata"),
                            thumbnail_path=f"{settings.API_V1_STR}/assets/thumbnail/{file['id']}" if file.get("hasThumbnail") else None,
                            subtitles=None
                        ))
                    elif file.get("name", "").endswith(".srt"):
                        try:
                            if not metadata["seasons"]["1"]["episodes"][-1]["subtitles"]:
                                metadata["seasons"]["1"]["episodes"][-1]["subtitles"] = []
                            metadata["seasons"]["1"]["episodes"][-1]["subtitles"].append(dict(
                                id=file["id"],
                                name=file["name"]
                            ))
                        except IndexError:
                            pass
                    # Season 1
                    elif file.get("mimeType", "").lower() == "application/vnd.google-apps.folder":
                        season = re.search(r"^s(?:\w+)? ?\-?\.?(\d{0,3})$", file["name"], flags=2)
                        season = season.group(1) if season else "1"
                        metadata["seasons"][season] = dict(episodes=[])
                        for episode_dir in self.get_files(folder_id=file["id"]):
                            # Loki E1
                            episode_metadata = {}
                            if episode_dir.get("mimeType", "").lower() == "application/vnd.google-apps.folder":
                                metadata["seasons"][season]["episodes"] = []
                                for episode_file in self.get_files(folder_id=episode_dir["id"]):
                                    # Loki E1 / ep1.mp4
                                    if "video" in episode_file.get("mimeType", "").lower():
                                        episode_metadata = {"subtitles": None}
                                        episode_metadata["id"] = episode_file["id"]
                                        episode_metadata["name"] = episode_file["name"]
                                        episode_metadata["modified_time"] = episode_file["modifiedTime"]
                                        episode_metadata["video_metadata"] = episode_file.get("videoMediaMetadata")
                                        episode_metadata["thumbnail_path"] = f"{settings.API_V1_STR}/assets/thumbnail/{episode_file['id']}" if episode_file.get("hasThumbnail") else None
                                        metadata["seasons"][season]["episodes"].append(episode_metadata)
                                    
                                    elif episode_file.get("name", "").endswith(".srt"):
                                        try:
                                            if not metadata["seasons"][season]["episodes"][-1]["subtitles"]:
                                                metadata["seasons"][season]["episodes"][-1]["subtitles"] = []
                                            metadata["seasons"][season]["episodes"][-1]["subtitles"].append(dict(
                                                id=episode_file["id"],
                                                name=episode_file["name"],
                                            ))
                                        except IndexError:
                                            pass
                            elif "video" in episode_dir.get("mimeType", "").lower():
                                episode_metadata = {"subtitles": None}
                                episode_metadata["id"] = episode_dir["id"]
                                episode_metadata["name"] = episode_dir["name"]
                                episode_metadata["modified_time"] = episode_dir["modifiedTime"]
                                episode_metadata["video_metadata"] = episode_dir.get("videoMediaMetadata")
                                episode_metadata["thumbnail_path"] = f"{settings.API_V1_STR}/assets/thumbnail/{episode_dir['id']}" if episode_dir.get("hasThumbnail") else None
                                metadata["seasons"][season]["episodes"].append(episode_metadata)
                            # for subs in Season 1
                            elif episode_dir.get("name", "").endswith(".srt"):
                                try:
                                    if not metadata["seasons"][season]["episodes"][-1]["subtitles"]:
                                        metadata["seasons"][season]["episodes"][-1]["subtitles"] = []
                                    metadata["seasons"][season]["episodes"][-1]["subtitles"].append(dict(
                                        id=episode_dir["id"],
                                        name=episode_dir["name"],
                                    ))
                                except IndexError:
                                    pass
                if metadata["seasons"]:
                    data.append(metadata)
        return data
    
    @classmethod
    def initialize_drive(cls, config) -> 'DriveAPI':
        if not config.get("gdrive_client_id"):
            config.set("gdrive_client_id", settings.GDRIVE_CLIENT_ID)
        if not config.get("gdrive_client_secret"):
            config.set("gdrive_client_secret", settings.GDRIVE_CLIENT_SECRET)
        if not config.get("gdrive_refresh_token"):
            config.set("gdrive_refresh_token", settings.GDRIVE_REFRESH_TOKEN)
        if not config.get("gdrive_access_token"):
            config.set("gdrive_access_token", settings.GDRIVE_ACCESS_TOKEN)
        if not config.get("gdrive_service_accounts_json"):
            config.set("gdrive_service_accounts_json", settings.GDRIVE_SERVICE_ACCOUNT_JSON)
        
        gdrive_service_accounts_json = config.get("gdrive_service_accounts_json")
        gdrive_service_accounts_json = False
        gdrive_client_id = config.get("gdrive_client_id")
        gdrive_client_secret = config.get("gdrive_client_secret")
        gdrive_refresh_token = config.get("gdrive_refresh_token")
        gdrive_access_token = config.get("gdrive_access_token")

        if sa_json := gdrive_service_accounts_json:
            print("Using service account json...")
            drive = cls.from_sa_json(random.choice(sa_json))
        elif (gdrive_client_id and gdrive_client_secret and gdrive_refresh_token and gdrive_access_token):
            print("Using client credentials...")
            drive = cls.from_gac_json(config.data)
        else:
            drive = cls()
        return drive