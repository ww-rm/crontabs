# -*- coding: UTF-8 -*-

import hashlib
from base64 import b64decode, b64encode
import json
from math import ceil
from os import PathLike
from pathlib import Path

from bs4 import BeautifulSoup
import requests

from .base import XSession, empty_retry
from datetime import datetime, timezone
from dateutil.parser import isoparse


class AliyunDriveBase(XSession):
    """Base api wrapper, don't use it directly."""

    url_host = "https://api.aliyundrive.com"

    passport_logout = "https://passport.aliyundrive.com/logout.htm"  # ?site=52&toURL=https://www.aliyundrive.com/"

    token_refresh = "https://api.aliyundrive.com/token/refresh"

    v2_file_get = "https://api.aliyundrive.com/v2/file/get"
    adrive_v2_file_createwithfolders = "https://api.aliyundrive.com/adrive/v2/file/createWithFolders"
    v2_file_complete = "https://api.aliyundrive.com/v2/file/complete"
    adrive_v3_file_search = "https://api.aliyundrive.com/adrive/v3/file/search"
    adrive_v3_file_list = "https://api.aliyundrive.com/adrive/v3/file/list"

    v2_user_get = "https://api.aliyundrive.com/v2/user/get"
    v2_recyclebin_trash = "https://api.aliyundrive.com/v2/recyclebin/trash"

    v2_databox_get_personal_info = "https://api.aliyundrive.com/v2/databox/get_personal_info"

    def _check_response(self, res: requests.Response) -> dict:
        """Check a json response."""

        # check empty response
        if res.status_code is None:
            return {}

        # check valid json data
        try:
            json_ = res.json()
        except ValueError:
            self.logger.error("{}:JsonValueError.".format(res.url))
            return {}

        # check error message
        if not res.ok:
            self.logger.error("{}:{}:{}".format(res.url, res.status_code, json_["message"]))
            return {}

        return json_

    def _get_logout(self) -> bool:
        res = self.get(
            AliyunDrive.passport_logout,
            params={
                "site": 52,
                "toURL": "https://www.aliyundrive.com/"
            }
        )
        if not res.ok:
            return False
        return True

    def _post_token_refresh(self, refresh_token: str) -> dict:
        """Get new access token.

        Args:
            refresh_token (str): get from self.refresh_token.

        Returns:
            See responses/aliyundrive/token_refresh.json
        """

        res = self.post(
            AliyunDriveBase.token_refresh,
            json={"refresh_token": refresh_token}
        )

        return self._check_response(res)

    ###################################
    ### User operations begin here. ###
    ###################################

    def _post_get_personal_info(self) -> dict:
        res = self.post(AliyunDriveBase.v2_databox_get_personal_info)

        return self._check_response(res)

    def _post_user_get(self) -> dict:
        res = self.post(AliyunDriveBase.v2_user_get)

        return self._check_response(res)

    ###################################
    ### File operations begin here. ###
    ###################################

    def _post_file_get(self, drive_id: str, file_id: str) -> dict:
        res = self.post(
            AliyunDriveBase.v2_file_get,
            json={
                "drive_id": drive_id,
                "file_id": file_id
            }
        )
        return self._check_response(res)

    def _post_file_create_with_folders(
        self,
        drive_id: str, name: str,
        parent_file_id: str = "root", type_: str = "file", check_name_mode: str = "refuse", *,
        part_info_list: list = None,
        size: int = 0, content_hash_name: str = "sha1", content_hash: str = "", proof_version: str = "v1", proof_code: str = ""
    ) -> dict:
        """Create file or folder tree.

        Args:
            drive_id (str): Id of drive to be operated.
            name (str): The path should be created, can be multi-level, (e.g. a/b/c/d/xxx.txt).
            parent_file_id (str): The parent node of node to be operated. Can be "root" or a string of node id.
            type_ (str): ["folder" | "file" ], decided by your leaf node of "name" param.
            check_name_mode (str): ["auto_rename" | "refuse" | "overwrite"]. "overwrite" only can be used in "file" type.

            part_info_list (list): How many parts you want to split file, and upload file in these parts.

            size (int): Size of upload file in bytes.
            content_hash_name (str): Hash type of arg `content_hash`.
            cotent_hash (str): Hash value of file.
            proof_version (str): Version of arg `proof_code`.
            proof_code (str): Used to proof you really own this file.

        Returns:
            See responses/aliyundrive/adrive_v2_file_createWithFolders.json
        """

        json_data = {
            "drive_id": drive_id,
            "name": name,
            "parent_file_id": parent_file_id,
            "type": type_,
            "check_name_mode": check_name_mode,
        }

        # add params of type file
        if type_ == "file":
            json_data["part_info_list"] = part_info_list

            # rapid upload
            if content_hash:
                json_data.update({
                    "size": size,
                    "content_hash_name": content_hash_name,
                    "content_hash": content_hash,
                    "proof_version": proof_version,
                    "proof_code": proof_code
                })

        res = self.post(
            AliyunDriveBase.adrive_v2_file_createwithfolders,
            json=json_data
        )

        return self._check_response(res)

    def _post_file_complete(self, drive_id: str, file_id: str, upload_id: str) -> dict:
        """Used to complete file upload.

        Args:
            drive_id (str): id
            file_id (str): get from return of post_file_create_with_folders.
            upload_id (str): get from return of post_file_create_with_folders.

        Returns:
            See responses/aliyundrive/v2_file_complete.json
        """

        res = self.post(
            AliyunDriveBase.v2_file_complete,
            json={
                "drive_id": drive_id,
                "file_id": file_id,
                "upload_id": upload_id
            }
        )

        return self._check_response(res)

    def _post_file_search(
        self,
        drive_id: str,
        query: str,
        limit: int = 100, order_by: str = "name ASC",
        *,
        image_thumbnail_process: str = "image/resize,w_400/format,jpeg",
        image_url_process: str = "image/resize,w_1920/format,jpeg",
        video_thumbnail_process: str = "video/snapshot,t_0,f_jpg,ar_auto,w_300"
    ) -> dict:
        """Search files in drive.

        Args:
            drive_id (str): Id of drive to search.
            query (str): Query statement.
            limit (int): Limit number of results.
            order_by (str): ["name ASC" | "updated_at ASC" | "created_at ASC" | "size ASC" | 
                "name DESC" | "updated_at DESC" | "created_at DESC" | "size DESC"]
        Returns:
            See responses/aliyundrive/adrive_v3_file_list.json
        """
        res = self.post(
            AliyunDriveBase.adrive_v3_file_search,
            json={
                "drive_id": drive_id,
                "query": query,
                "limit": limit,
                "order_by": order_by,
                "image_thumbnail_process": image_thumbnail_process,
                "image_url_process": image_url_process,
                "video_thumbnail_process": video_thumbnail_process
            }
        )

        return self._check_response(res)

    def _post_file_list(
        self,
        drive_id: str, parent_file_id: str = "root",
        order_by: str = "name", order_direction: str = "ASC", limit: int = 100,
        *,
        all_: bool = False,  fileds: str = "*",
        url_expire_sec: int = 1600,
        image_thumbnail_process: str = "image/resize,w_400/format,jpeg",
        image_url_process: str = "image/resize,w_1920/format,jpeg",
        video_thumbnail_process: str = "video/snapshot,t_0,f_jpg,ar_auto,w_300"
    ) -> dict:
        """List items of a folder node.

        Args:
            drive_id: ID.
            parent_file_id (str): The parent folder of folder to be operated. Can be "root" or a string of file id.
            limit (int): Limit number of results.
            order_by (str): ["name", "updated_at", "created_at", "size"]
            order_direction (str): ["ASC" | "DESC"]
        """

        res = self.post(
            AliyunDriveBase.adrive_v3_file_list,
            json={
                "drive_id": drive_id,
                "parent_file_id": parent_file_id,
                "limit": limit,
                "order_by": order_by,
                "order_direction": order_direction,
                "all": all_,
                "fields": fileds,
                "url_expire_sec": url_expire_sec,
                "image_thumbnail_process": image_thumbnail_process,
                "image_url_process": image_url_process,
                "video_thumbnail_process": video_thumbnail_process
            }
        )

        return self._check_response(res)


class AliyunDrive(AliyunDriveBase):
    """
    """
    """
    https://auth.aliyundrive.com/v2/oauth/authorize -> Cookie: SESSIONID
    https://passport.aliyundrive.com/mini_login.htm -> Cookie: cookie2, t, XSRF-TOKEN. "form-data"
    https://ynuf.aliapp.org/w/wu.json -> Cookie: cbc
    https://ynuf.aliapp.org/service/um.json -> Res: tn, id
    https://passport.aliyundrive.com/newlogin/login.do -> bizExt
    https://auth.aliyundrive.com/v2/oauth/token_login -> ...

    """

    def __init__(self, interval: float = 0.01) -> None:
        super().__init__(interval=interval)
        self.user_id = ""
        self.drive_id = ""

        self.token_type = ""  # generally "Bearer"
        self.access_token = ""  # access token added to "Authorization" header
        self.refresh_token = ""  # token used to refresh access token

        self.expire_time = datetime.now(timezone.utc)  # access token expire time

    def _get_proof_code(self, filepath: PathLike, version: str = "v1") -> str:
        """Get proof_code of content by access token.

        Args:
            filepath (PathLike): Path of file need to calculate proof_code.
            version (str): Can be "v1".

        Returs:
            str: proof_code.

        Note:

        ```js
        static async GetBuffHashProof(access_token: string, buff: Buffer) {
            if (buff.length == 0) return { sha1: 'DA39A3EE5E6B4B0D3255BFEF95601890AFD80709', proof_code: '' };
            let hash = await sha1(buff);
            hash = hash.toUpperCase();
            const m = unescape(encodeURIComponent(access_token));
            const buffa = Buffer.from(m);
            const md5a = await md5(buffa);
            const start = Number(BigInt('0x' + md5a.substr(0, 16)) % BigInt(buff.length));
            const end = Math.min(start + 8, buff.length);
            const buffb = buff.slice(start, end);
            const proof_code = buffb.toString('base64');

            return { sha1: hash, proof_code };
        }
        ```
        """

        filepath = Path(filepath)
        file_size = filepath.stat().st_size
        if file_size <= 0:
            return ""

        if version == "v1":
            md5_token = hashlib.md5(self.access_token.encode("utf8")).hexdigest()
            start = int(md5_token[0:16], 16) % file_size
            with filepath.open("rb") as f:
                f.seek(start)
                proof_code = b64encode(f.read(8))
        else:
            raise ValueError("version must be v1")

        return proof_code

    def _check_refresh(self) -> bool:
        """Check token and try refresh it if is about to expire.

        Used before each api call.
        """

        # if expire in 5 min
        if (self.expire_time - datetime.now(timezone.utc)).total_seconds() <= 5*60:
            self.logger.warning("Token is about to expire, try to auto refresh.")

            # try refresh token
            refresh_info = self._post_token_refresh(self.refresh_token)
            if not refresh_info:
                self.logger.error("Refresh token failed.")
                return False

            # set new token info
            self.token_type = refresh_info["token_type"]
            self.access_token = refresh_info["access_token"]
            self.refresh_token = refresh_info["refresh_token"]

            self.expire_time = isoparse(refresh_info["expire_time"])  # include timezone, utc time

            self.headers["Authorization"] = self.token_type + " " + self.access_token

        return True

    def login(self, usrn: str, pwd: str, *, bizExt: str = "", cookies: dict = None) -> bool:
        """Login.

        Args:
            usrn (str): Username.
            pwd (str): Password.
        """

        # TODO: usrn and pwd login

        if usrn and pwd:
            raise NotImplementedError
        else:
            if not bizExt:
                return False

            login_info = b64decode(bizExt).decode("gbk")
            login_result = json.loads(login_info)["pds_login_result"]
            if not login_result:
                return False

            self.user_id = login_result["userId"]
            self.drive_id = login_result["defaultDriveId"]

            self.token_type = login_result["tokenType"]
            self.access_token = login_result["accessToken"]
            self.refresh_token = login_result["refreshToken"]

            self.expire_time = isoparse(login_result["expireTime"])  # include timezone, utc time

            self.headers["Authorization"] = self.token_type + " " + self.access_token

            if cookies:
                self.cookies.update(cookies)

            return True

    def logout(self) -> bool:
        ret = self._get_logout()

        return ret

    def create_folder(
        self,
        folder_path: PathLike,
        parent_file_id: str = "root", check_name_mode: str = "refuse"
    ) -> dict:
        """Create folder of specified path in drive.

        Args:
            folder_path (PathLike): The full path of folder to be created, can be multi-level.
            parent_file_id (str): The parent node of node to be operated. Can be "root" or a string of node id.
            check_name_mode (str): Can be "auto_rename" or "refuse".

        Returns:
            Return empty if failed, 
            else see responses/aliyundrive/adrive_v2_file_createWithFolders.json
        """

        folder_path = Path(folder_path)

        if check_name_mode == "auto_rename":
            self.logger.warning("Check name mode is auto_rename for create folder {}.".format(folder_path.as_posix()))

        if not self._check_refresh():
            return {}
        create_info = self._post_file_create_with_folders(
            self.drive_id,
            folder_path.as_posix(),
            parent_file_id, "folder", check_name_mode
        )

        if not create_info:
            self.logger.error("Failed to create folder {}.".format(folder_path.as_posix()))
            return {}

        if check_name_mode == "refuse" and create_info.get("exist") is True:
            self.logger.warning("Folder {} already exist.".format(folder_path.as_posix()))

        self.logger.info("Successfully create folder {}.".format(folder_path.as_posix()))
        return create_info

    def upload_file(
        self,
        file_upload_path: PathLike, file_local_path: PathLike,
        parent_file_id: str = "root", check_name_mode: str = "refuse", try_rapid_upload: bool = True
    ) -> dict:
        """Upload a file to specified path.

        Args:
            file_upload_path (PathLike): The full path of file to upload, include full filename and suffix.
            file_local_path (PathLike): The local path of file to upload.
            parent_file_id (str): The parent node of node to be operated. Can be "root" or a string of node id.
            check_name_mode (str): ["auto_rename" | "refuse" | "overwrite"].
            try_rapid_upload (bool): If try rapid upload, will take time to calc sha1 and proof code.

        Returns:
            Return empty if failed,
            else see responses/aliyundrive/adrive_v2_file_createWithFolders.json
                and responses/aliyundrive/v2_file_complete.json
        """

        CHUNK_SIZE = 10*1024*1024

        filepath = Path(file_local_path)

        # decide whether to split file
        file_size = filepath.stat().st_size

        part_info_list = []
        for i in range(ceil(file_size / CHUNK_SIZE) or 1):
            # at least one part
            part_info_list.append({"part_number": i + 1})

        # init with empty str
        content_hash = ""
        proof_code = ""

        # process rapid upload
        if try_rapid_upload:
            # calculate sha1 hash
            content_hash = hashlib.sha1()
            with filepath.open("rb") as f:
                while True:
                    # 10 MB each time
                    chunk = f.read(10*1024*1024)
                    if not chunk:
                        break
                    content_hash.update(chunk)
            content_hash = content_hash.hexdigest().upper()

            # caculate proof code
            proof_code = self._get_proof_code(filepath, "v1")

        if not self._check_refresh():
            return {}
        create_info = self._post_file_create_with_folders(
            self.drive_id,
            Path(file_upload_path).as_posix(),
            parent_file_id, "file", check_name_mode,
            part_info_list=part_info_list,
            size=file_size,
            content_hash_name="sha1", content_hash=content_hash,
            proof_version="v1", proof_code=proof_code
        )

        if not create_info:
            self.logger.error("Failed to get create info of file {}.".format(filepath.as_posix()))
            return {}

        # check upload id
        if not create_info.get("upload_id"):
            if check_name_mode == "refuse":
                self.logger.warning("Same file found, file {} upload refused".format(filepath.as_posix()))
                return create_info
            else:
                self.logger.error("Failed get upload id for file".format(filepath.as_posix()))
                return {}

        # rapid upload successfully
        if create_info.get("rapid_upload") is True:
            self.logger.info("Rapid upload file {}".format(filepath.as_posix()))
            return create_info

        # upload file chunks
        with filepath.open("rb") as f:
            for part_info in create_info["part_info_list"]:
                upload_url = part_info["upload_url"]
                chunk = f.read(CHUNK_SIZE)

                # try 3 times
                flag = False
                for _ in range(3):
                    res = self.put(upload_url, data=chunk)
                    if res.ok:
                        flag = True
                        break
                if not flag:
                    self.logger.error("File {} Part {} upload failed.".format(filepath.as_posix(), part_info["part_number"]))
                    return {}

        if not self._check_refresh():
            return {}
        complete_info = self._post_file_complete(
            self.drive_id,
            create_info["file_id"],
            create_info["upload_id"]
        )
        if not complete_info:
            self.logger.error("Failed to complete upload file {}.".format(filepath.as_posix()))
            return {}

        self.logger.info("Successfully upload file {}.".format(filepath.as_posix()))
        return complete_info

    def search_file(
        self,
        name: str,
        order_by: str = "name", order_direction: str = "ASC", limit: int = 100, exact_match: bool = True, *,
        category: str = "", parent_file_id: str = ""
    ) -> dict:
        """Search files in specified folder and path.

        Args:
            name (str): Name to search.
            order_by (str): ["name", "updated_at", "created_at", "size"]
            order_direction (str): ["ASC" | "DESC"]
            limit (int): Limit number of results.
            exact_match (bool): Whether exactly match name.

            category (str): Search file type, ["image" | "video" | "folder" | "doc" | "audio"].
            parent_file_id (str): The parent file id. Can be "root" or a string of file id. If empty string, search in total drive.

        Returns:
            Return empty when failed, else see response folder.
        """

        query = "(name {} \"{}\")".format("=" if exact_match else "match", name)

        if parent_file_id:
            query += " and (parent_file_id = \"{}\"".format(parent_file_id)

        if category:
            query += " and (category = \"{}\"".format(category)

        if not self._check_refresh():
            return {}
        search_info = self._post_file_search(
            self.drive_id,
            query,
            limit,
            order_by+" "+order_direction,
        )

        if not search_info:
            self.logger.error("Failed to search file {}.".format(name))
            return {}
        return search_info

    def list_file(
        self, parent_file_id: str = "root",
        order_by: str = "name", order_direction: str = "ASC", limit: int = 100
    ) -> dict:
        """List files in a folder.

        Args:
            parent_file_id (str): The parent file id. Can be "root" or a string of file id.
            order_by (str): ["name", "updated_at", "created_at", "size"]
            order_direction (str): ["ASC" | "DESC"]
            limit (int): Limit number of results.

        Returns:
            Return empty when failed, else see responses folder.
        """

        if not self._check_refresh():
            return {}
        list_info = self._post_file_list(
            self.drive_id, parent_file_id,
            order_by, order_direction, limit
        )

        if not list_info:
            self.logger.error("Failed to list folder {}.".format(parent_file_id))
            return {}
        return list_info

    def delete_file(self, file_id: str):
        """Move file or folder to trash."""

    def download_file(self, file_id: str, file_save_path: PathLike):
        "Download a file to local storage."
