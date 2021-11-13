import json
import logging
from base64 import b64decode
from datetime import datetime, timezone
from os import PathLike

from dateutil.parser import isoparse

from . import xsession


class PyliyunDrive:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.s = xsession.AliyunDrive()
        self.s.headers.update(self.headers)

        self.user_id = ""
        self.drive_id = ""

        self.token_type = ""  # generally "Bearer"
        self.access_token = ""  # access token added to "Authorization" header
        self.refresh_token = ""  # token used to refresh access token

        self.expire_time = datetime.now(timezone.utc)  # access token expire time

    def _check_refresh(self) -> bool:
        # if expire in 5 min
        if (self.expire_time - datetime.now(timezone.utc)).seconds <= 5*60:
            self.logger.warning("PyliyunDrive:Token is about to expire, auto refresh.")

            # try refresh token
            refresh_info = self.s.post_token_refresh(self.refresh_token)
            if not refresh_info:
                self.logger.error("PyliyunDrive:Refresh token failed.")
                return False

            # set new token info
            self.token_type = refresh_info.get("token_type")
            self.access_token = refresh_info.get("access_token")
            self.refresh_token = refresh_info.get("refresh_token")

            self.expire_time = isoparse(refresh_info.get("expire_time"))  # include timezone, utc time

            self.s.headers["Authorization"] = self.token_type + " " + self.access_token

        return True

    def _debug_login(self, bizExt: str, cookies: dict = None) -> bool:
        """Used for debug."""
        login_info = b64decode(bizExt).decode("gbk")
        login_result = json.loads(login_info).get("pds_login_result")
        if not login_result:
            return False

        self.user_id = login_result.get("userId")
        self.drive_id = login_result.get("defaultDriveId")

        self.token_type = login_result.get("tokenType")
        self.access_token = login_result.get("accessToken")
        self.refresh_token = login_result.get("refreshToken")

        self.expire_time = isoparse(login_result.get("expireTime"))  # include timezone, utc time

        self.s.headers["Authorization"] = self.token_type + " " + self.access_token

        if cookies:
            self.s.cookies.update(cookies)

    def login(self, usrn: str, pwd: str, *, bizExt: str = None, cookies: dict = None) -> bool:
        ...

    def logout(self) -> bool:
        ...

    def create_floder(self, full_folder_path: PathLike) -> bool:
        ...

        if not self._check_refresh():
            return False

        self.s.post_file_create_with_folders

        return True

    def upload_file(self, upload_path: PathLike, local_path: PathLike) -> bool:
        ...
        if not self._check_refresh():
            return False

        self.s.post_file_create_with_folders
        self.s.post_file_complete

        return True
