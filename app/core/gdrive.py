import random
import re
from typing import Any, Dict, List, Optional, Union

import httplib2
from app.settings import settings
from googleapiclient.discovery import Resource, build
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials


class GdriveNotInitialized(Exception):
    pass


class DriveAPI:
    def __init__(
        self,
        account_credentials: Optional[Union[GoogleCredentials, Dict[str, Any]]] = None,
        service_account_credentials: Optional[
            Union[ServiceAccountCredentials, Dict[str, Any]]
        ] = None,
    ) -> None:

        self.fully_initialized = False
        self.token_uri = "https://accounts.google.com/o/oauth2/token"
        self.scopes = ["https://www.googleapis.com/auth/drive"]

        if account_credentials and not isinstance(
            account_credentials, GoogleCredentials
        ):
            account_credentials = GoogleCredentials(
                client_id=account_credentials["gdrive_client_id"],
                access_token=account_credentials["gdrive_access_token"],
                client_secret=account_credentials["gdrive_client_secret"],
                refresh_token=account_credentials["gdrive_refresh_token"],
                token_uri=self.token_uri,
                token_expiry=None,
                user_agent=None,
            )
        if service_account_credentials and not isinstance(
            service_account_credentials, ServiceAccountCredentials
        ):
            service_account_credentials = (
                ServiceAccountCredentials.from_json_keyfile_dict(
                    keyfile_dict=service_account_credentials,
                    token_uri=self.token_uri,
                    scopes=self.scopes,
                )
            )

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
    def from_sa_json(cls, json: Dict[str, Any]) -> "DriveAPI":
        return cls(
            account_credentials=None,
            service_account_credentials=json,
        )

    @classmethod
    def from_gac_json(cls, json: Dict[str, Any]) -> "DriveAPI":
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
            supportsAllDrives=True,
            fields="thumbnailLink",
            fileId=file_id,
        ).execute()
        if thumb := response.get("thumbnailLink"):
            return re.sub(r"=s\d+$", "", thumb)

    def get_files(self, folder_id):
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        page_token = None
        while True:
            response = self.files.list(
                pageToken=page_token,
                supportsAllDrives=True,
                pageSize=200,
                includeItemsFromAllDrives=True,
                fields="files(\
                    id,\
                    name,\
                    parents,\
                    mimeType,\
                    modifiedTime,\
                    hasThumbnail,\
                    shortcutDetails,\
                    videoMediaMetadata \
                ), incompleteSearch, nextPageToken",
                q=f"'{folder_id}' in parents \
                    and trashed = false \
                    and (\
                        mimeType = 'text/plain' \
                        or mimeType contains 'video' \
                        or mimeType = 'application/octet-stream'\
                        or mimeType = 'application/vnd.google-apps.folder' \
                        or mimeType = 'application/vnd.google-apps.shortcut' \
                    )",
                orderBy="name",
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
            page_token = response.get("nextPageToken")
            if page_token is None:
                return

    def dig_folders(
        self, folder_id: str, data: Optional[List[Dict[str, Any]]] = []
    ) -> None:
        if not self.fully_initialized:
            raise GdriveNotInitialized()
        for file in self.get_files(folder_id):
            print(f"Digged '{file.get('name')}'")
            if file["mimeType"] == "application/vnd.google-apps.folder":
                self.dig_folders(file["id"], data)
            else:
                data.append(file)

    @classmethod
    def initialize_drive(cls, config) -> "DriveAPI":
        if not config.get("gdrive_client_id"):
            config.set("gdrive_client_id", settings.GDRIVE_CLIENT_ID)
        if not config.get("gdrive_client_secret"):
            config.set("gdrive_client_secret", settings.GDRIVE_CLIENT_SECRET)
        if not config.get("gdrive_refresh_token"):
            config.set("gdrive_refresh_token", settings.GDRIVE_REFRESH_TOKEN)
        if not config.get("gdrive_access_token"):
            config.set("gdrive_access_token", settings.GDRIVE_ACCESS_TOKEN)
        if not config.get("gdrive_service_accounts_json"):
            config.set(
                "gdrive_service_accounts_json", settings.GDRIVE_SERVICE_ACCOUNT_JSON
            )

        gdrive_service_accounts_json = config.get("gdrive_service_accounts_json")
        gdrive_service_accounts_json = False
        gdrive_client_id = config.get("gdrive_client_id")
        gdrive_client_secret = config.get("gdrive_client_secret")
        gdrive_refresh_token = config.get("gdrive_refresh_token")
        gdrive_access_token = config.get("gdrive_access_token")

        if sa_json := gdrive_service_accounts_json:
            print("Using service account json...")
            drive = cls.from_sa_json(random.choice(sa_json))
        elif (
            gdrive_client_id
            and gdrive_client_secret
            and gdrive_refresh_token
            and gdrive_access_token
        ):
            print("Using client credentials...")
            drive = cls.from_gac_json(config.data)
        else:
            drive = cls()
        return drive
