# -*- coding: UTF-8 -*-

import hashlib
from base64 import b64decode, b64encode
from math import ceil
from os import PathLike
from pathlib import Path

from bs4 import BeautifulSoup

from .base import XSession, empty_retry


class AliyunDriveBase(XSession):
    """
    https://auth.aliyundrive.com/v2/oauth/authorize -> Cookie: SESSIONID
    https://passport.aliyundrive.com/mini_login.htm -> Cookie: cookie2, t, XSRF-TOKEN. "form-data"
    https://ynuf.aliapp.org/w/wu.json -> Cookie: cbc
    https://ynuf.aliapp.org/service/um.json -> Res: tn, id
    https://passport.aliyundrive.com/newlogin/login.do -> bizExt
    https://auth.aliyundrive.com/v2/oauth/token_login -> ...

    """

    url_host = "https://api.aliyundrive.com"

    passport_logout = "https://passport.aliyundrive.com/logout.htm"  # ?site=52&toURL=https://www.aliyundrive.com/"

    token_refresh = "https://api.aliyundrive.com/token/refresh"

    adrive_v2_file_createwithfolders = "https://api.aliyundrive.com/adrive/v2/file/createWithFolders"
    adrive_v2_file_complete = "https://api.aliyundrive.com/v2/file/complete"
    adrive_v3_file_search = "https://api.aliyundrive.com/adrive/v3/file/search"
    adrive_v3_file_list = "https://api.aliyundrive.com/adrive/v3/file/list"

    v2_user_get = "https://api.aliyundrive.com/v2/user/get"
    v2_recyclebin_trash = "https://api.aliyundrive.com/v2/recyclebin/trash"

    adrive_v2_databox_get_personal_info = "https://api.aliyundrive.com/v2/databox/get_personal_info"

    def _get_proof_code(self, filepath: PathLike, version: str = "v1") -> str:
        """
        Get proof_code of content by access token.

        Args:
            filepath (PathLike): path of file need to calculate proof_code.
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

    def get_logout(self) -> bool:
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

    def post_token_refresh(self, refresh_token: str) -> dict:
        """
        Get new access token.

        Args:
            refresh_token (str): get from self.refresh_token.

        Returns:
            See responses/aliyundrive/token_refresh.json
        """

        res = self.post(AliyunDrive.token_refresh, json={"refresh_token": refresh_token})

        if res.status_code != 200:
            return {}
        return res.json()

    def post_file_create_with_folders(
        self,
        drive_id: str, name: str,
        parent_file_id: str = "root", type_: str = "file", check_name_mode: str = "refuse", *,
        filepath: PathLike = None, try_rapid_upload: bool = True
    ) -> dict:
        """
        Create node with folders in drive.

        Args:
            drive_id (str): Id of drive to be operated.
            name (str): The path should be created, can be multi-level, (e.g. a/b/c/d/xxx.txt).
            parent_file_id (str): The parent node of node to be operated. Can be "root" of a string of node id.
            type_ (str): ["folder" | "file" ], decided by your leaf node of "name" param.
            check_name_mode (str): ["auto_rename" | "refuse" | "overwrite"].
            filepath (Pathlike): file path to be uploaded.
            try_rapid_upload (bool): if try rapid upload, will take time to calc sha1 and proof code.

        Returns:
            See responses/aliyundrive/adrive_v2_file_createWithFolders.json

            Returns empty dict when upload failed.
        """
        chunk_size = 10*1024*1024

        json_data = {
            "drive_id": drive_id,
            "name": name,
            "parent_file_id": parent_file_id,
            "type": type_,
            "check_name_mode": check_name_mode,
        }

        # prepare file json params
        if type_ == "file":
            filepath = Path(filepath)

            # decide whether to split file
            file_size = filepath.stat().st_size
            json_data["size"] = file_size

            json_data["part_info_list"] = []
            for i in range(ceil(file_size / chunk_size) or 1):
                # at least one part
                json_data["part_info_list"].append({"part_number": i + 1})

            # process rapid upload
            if try_rapid_upload:
                # calculate sha1 hash
                json_data["content_hash_name"] = "sha1"

                content_hash = hashlib.sha1()
                with filepath.open("rb") as f:
                    while True:
                        # 10 MB each time
                        chunk = f.read(10*1024*1024)
                        if not chunk:
                            break
                        content_hash.update(chunk)
                json_data["content_hash"] = content_hash.hexdigest().upper()

                # caculate proof code
                json_data["proof_version"] = "v1"
                json_data["proof_code"] = self._get_proof_code(filepath)

        # print(json_data)
        res = self.post(
            AliyunDrive.adrive_v2_file_createwithfolders,
            json=json_data
        )

        if res.status_code != 201:
            self.logger.error("Aliyundrive:createwithfolders failed:{}.".format(res.status_code))
            return {}

        create_info = res.json()

        if type_ == "file":
            # check upload id
            if not create_info.get("upload_id"):
                if check_name_mode == "refuse":
                    self.logger.warning("Same file found, {} upload refused".format(filepath.as_posix()))
                    return create_info
                else:
                    self.logger.error("Failed get upload id:{}".format(filepath.as_posix()))
                    return {}

            # rapid upload successfully
            if create_info.get("rapid_upload"):
                self.logger.info("Aliyundrive:rapid upload file {}".format(filepath.as_posix()))
                return create_info

            # upload file chunks
            with filepath.open("rb") as f:
                for part_info in create_info.get("part_info_list"):
                    upload_url = part_info.get("upload_url")
                    chunk = f.read(chunk_size)

                    # try 3 times
                    flag = False
                    for _ in range(3):
                        res = self.put(upload_url, data=chunk)
                        if res.ok:
                            flag = True
                            break
                    if not flag:
                        self.logger.error("AliyunDrive:File {} Part {} upload failed.".format(filepath.as_posix(), part_info.get("part_number")))
                        return {}

        return create_info

    def post_file_complete(self, drive_id: str, file_id: str, upload_id: str):
        """
        Must be used after method post_file_create_with_folders without rapid upload.

        Args:
            drive_id: id
            file_id: get from return of post_file_create_with_folders.
            upload_id: get from return of post_file_create_with_folders.

        Returns:
            See responses/aliyundrive/adrive_v2_file_complete.json
        """

        res = self.post(
            AliyunDrive.adrive_v2_file_complete,
            json={
                "drive_id": drive_id,
                "file_id": file_id,
                "upload_id": upload_id
            }
        )

        if res.status_code != 200:
            return {}

        return res.json()

    def post_file_search(self, drive_id: str, name: str, parent_file_id: str = "root", limit: int = 100, order_by: str = "name ASC"):
        """
        Search files in drive.

        Args:
            drive_id (str): Id of drive to search.
            name (str): Name of node to be operated.
            parent_file_id (str): The parent folder of folder to be operated. Can be "root" of a string of file id.
            limit (int): Limit number of results.
            order_by (str): [name ASC].

        Returns:

        """
        query = "parent_file_id = \"{}\" and (name = \"{}\"".format(parent_file_id, name)


class AliyunDrive(AliyunDriveBase):
    """"""
