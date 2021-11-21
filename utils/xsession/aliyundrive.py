# -*- coding: UTF-8 -*-

import hashlib
from base64 import b64decode, b64encode
import json
from math import ceil
from os import PathLike
from pathlib import Path
from typing import Tuple
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from bs4 import BeautifulSoup
import requests

from .base import XSession, empty_retry
from datetime import datetime, timezone
from dateutil.parser import isoparse
import re


class AliyunDriveBase(XSession):
    """Base api wrapper, don't use it directly."""

    URL_host = "https://api.aliyundrive.com"

    URL_sign_in = "https://www.aliyundrive.com/sign/in"

    # ?client_id=25dzX3vbYqktVxyX&redirect_uri=https://www.aliyundrive.com/sign/callback&response_type=code&login_type=custom&state={"origin":"https://www.aliyundrive.com"}"
    URL_auth_v2_oauth_authorize = "https://auth.aliyundrive.com/v2/oauth/authorize"
    URL_auth_v2_oauth_token_login = "https://auth.aliyundrive.com/v2/oauth/token_login"

    # lang=zh_cn&appName=aliyun_drive&appEntrance=web&styleType=auto&bizParams=&notLoadSsoView=false&notKeepLogin=false&isMobile=false&ad__pass__q__rememberLogin=false&ad__pass__q__forgotPassword=false&ad__pass__q__licenseMargin=false&ad__pass__q__loginType=normal&hidePhoneCode=true&rnd=0.9290066682151727
    URL_passport_mini_login = "https://passport.aliyundrive.com/mini_login.htm"

    URL_passport_newlogin_login = "https://passport.aliyundrive.com/newlogin/login.do"  # ?appName=aliyun_drive&fromSite=52&_bx-v=2.0.31"

    URL_passport_logout = "https://passport.aliyundrive.com/logout.htm"  # ?site=52&toURL=https://www.aliyundrive.com/"

    URL_token_get = "https://api.aliyundrive.com/token/get"
    URL_token_refresh = "https://api.aliyundrive.com/token/refresh"

    URL_v2_file_get = "https://api.aliyundrive.com/v2/file/get"
    URL_adrive_v2_file_createwithfolders = "https://api.aliyundrive.com/adrive/v2/file/createWithFolders"
    URL_v2_file_complete = "https://api.aliyundrive.com/v2/file/complete"
    URL_adrive_v3_file_search = "https://api.aliyundrive.com/adrive/v3/file/search"
    URL_adrive_v3_file_list = "https://api.aliyundrive.com/adrive/v3/file/list"

    URL_v2_user_get = "https://api.aliyundrive.com/v2/user/get"
    URL_v2_recyclebin_trash = "https://api.aliyundrive.com/v2/recyclebin/trash"

    URL_v2_databox_get_personal_info = "https://api.aliyundrive.com/v2/databox/get_personal_info"

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

    def _get_sign_in(self) -> str:
        """Get sign in html page."""

        res = self.get(AliyunDriveBase.URL_sign_in)

        if res.status_code != 200:
            return ""
        return res.text

    ###################################
    ### Auth operations begin here. ###
    ###################################

    def _get_v2_oauth_authorize(
        self, client_id: str,
        redirect_url: str = "https://www.aliyundrive.com/sign/callback",
        *,
        response_type: str = "code", login_type: str = "custom", state: dict = None
    ) -> str:
        """Get SESSIONID cookie.

        Args:
            client_id: get from self._get_client_id.

        Returns:
            Html page text.
        """
        res = self.get(
            AliyunDriveBase.URL_auth_v2_oauth_authorize,
            params={
                "client_id": client_id,
                "redirect_url": redirect_url,
                "response_type": response_type,
                "login_type": login_type,
                "state": state
            }
        )

        if res.status_code != 200:
            return ""
        return res.text

    def _post_token_login(self, token: str) -> dict:
        """Token login.

        Args:
            token (str): get from `accessToken` in passport login return data `bizExt`.
        """

        res = self.post(
            AliyunDriveBase.URL_auth_v2_oauth_token_login,
            json={"token": token}
        )

        if res.status_code != 200:
            return {}
        return res.json()

    def _get_passport_mini_login(
        self,
        appName="aliyun_drive",
        appEntrance="web",
        styleType="auto",
        bizParams="",
        isMobile=False,
        lang="zh_cn",
        rnd=0.9290066682151727,
        notLoadSsoView=False,
        notKeepLogin=False,
        hidePhoneCode=True,
        ad__pass__q__rememberLogin=False,
        ad__pass__q__forgotPassword=False,
        ad__pass__q__licenseMargin=False,
        ad__pass__q__loginType="normal"
    ) -> str:
        """Get cookies and login form data from html page.

        Returns:
            Html page text.

        Cookies:
            cookie2, XSRF-TOKEN
        """

        res = self.get(
            AliyunDriveBase.URL_passport_mini_login,
            params={
                "appName": appName,
                "appEntrance": appEntrance,
                "styleType": styleType,
                "bizParams": bizParams,
                "isMobile": str(isMobile).lower(),
                "lang": lang,
                "rnd": rnd,
                "notLoadSsoView": str(notLoadSsoView).lower(),
                "notKeepLogin": str(notKeepLogin).lower(),
                "hidePhoneCode": str(hidePhoneCode).lower(),
                "ad__pass__q__rememberLogin": str(ad__pass__q__rememberLogin).lower(),
                "ad__pass__q__forgotPassword": str(ad__pass__q__forgotPassword).lower,
                "ad__pass__q__licenseMargin": str(ad__pass__q__licenseMargin).lower(),
                "ad__pass__q__loginType": ad__pass__q__loginType
            }
        )

        if res.status_code != 200:
            return ""
        return res.text

    def _post_passport_newlogin_login(
        self,
        loginId: str,
        password2: str,
        keepLogin: bool = False,
        *,
        loginFormData: dict = None,
        navUserAgent: str = "",
        navlanguage: str = "zh-CN",
        navPlatform: str = "Win32",
        umidGetStatusVal: int = 255,
        screenPixel: str = "1280x720",
        ua: str = "",
        deviceId: str = "",
        bx_ua: str = "",
        bx_umidtoken: str = "",
        appName: str = "aliyun_drive",
        fromSite: int = 52,
        _bx_v: str = "2.0.31",

    ) -> dict:
        """
        Args:
            loginFormData: Get from mini login html page, include `appName`, `appEntrance`, `_csrf_token`, `umidToken`, `isMobile`, `lang`, `returnUrl`, `hsiz`, `fromSite`, `bizParams` fields.
            navUserAgent: Same as UA header.

            appName: Used in params.
            fromSite: Used in params.
            _bx-v: Used in params.

        Note:
            2021.11.19. Actually only need `loginId`, `password2`, `keepLogin` fileds.
        """
        login_data = {
            "loginId": loginId,
            "password2": password2,
            "keepLogin": keepLogin,
        }

        if ua:
            login_data1 = {
                "navUserAgent": navUserAgent,
                "navlanguage": navlanguage,
                "navPlatform": navPlatform,
                "screenPixel": screenPixel,
                "umidGetStatusVal": umidGetStatusVal,
                "ua": ua,
            }
            login_data1.update(loginFormData)
            login_data.update(login_data1)

        if bx_ua:
            login_data2 = {
                "deviceId": deviceId,
                "bx-ua": bx_ua,
                "bx-umidtoken": bx_umidtoken,
            }
            login_data.update(login_data2)

        login_params = {
            "appName": appName,
            "fromSite": fromSite,
            "_bx-v": _bx_v
        }

        res = self.post(
            AliyunDriveBase.URL_passport_newlogin_login,
            params=login_params,
            data=login_data,
        )

        if res.status_code != 200:
            return {}

        # DEBUG
        # print(res.text)

        try:
            json_ = res.json()
        except ValueError:
            self.logger.error("JsonDeodeError.")
            return {}

        if json_.get("content", None) is None:
            return {}
        return json_["content"]["data"]

    def _get_logout(self) -> bool:
        res = self.get(
            AliyunDrive.URL_passport_logout,
            params={
                "site": 52,
                "toURL": "https://www.aliyundrive.com/"
            }
        )
        if not res.ok:
            return False
        return True

    def _post_token_get(self, code: str, deviceId: str, loginType: str = "normal") -> dict:
        """Get refresh token.

        Args:
            code: get from self._get_token_login
            deviceId: `cna` cookie.
        """

        res = self.post(
            AliyunDriveBase.URL_token_get,
            json={
                "code": code,
                "deviceId": deviceId,
                "loginType": loginType
            }
        )

        return self._check_response(res)

    def _post_token_refresh(self, refresh_token: str) -> dict:
        """Get new access token.

        Args:
            refresh_token (str): get from self.refresh_token.

        Returns:
            See responses/aliyundrive/token_refresh.json
        """

        res = self.post(
            AliyunDriveBase.URL_token_refresh,
            json={"refresh_token": refresh_token}
        )

        return self._check_response(res)

    ###################################
    ### User operations begin here. ###
    ###################################

    def _post_get_personal_info(self) -> dict:
        res = self.post(AliyunDriveBase.URL_v2_databox_get_personal_info)

        return self._check_response(res)

    def _post_user_get(self) -> dict:
        res = self.post(AliyunDriveBase.URL_v2_user_get)

        return self._check_response(res)

    ###################################
    ### File operations begin here. ###
    ###################################

    def _post_file_get(self, drive_id: str, file_id: str) -> dict:
        res = self.post(
            AliyunDriveBase.URL_v2_file_get,
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
            AliyunDriveBase.URL_adrive_v2_file_createwithfolders,
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
            AliyunDriveBase.URL_v2_file_complete,
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
            AliyunDriveBase.URL_adrive_v3_file_search,
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
            AliyunDriveBase.URL_adrive_v3_file_list,
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

    @staticmethod
    def _rsa_encrypt(plain: str, n: str, e: str = "10001") -> str:
        """RSA encrypt.

        Args:
            n: Modulus in hex string.
            e: Exponent in hex string.

        Returns:
            str: Cipher in hex string.
        """
        key = RSA.construct((int(n, 16), int(e, 16)))
        encrypter = PKCS1_v1_5.new(key)

        cipher = encrypter.encrypt(plain.encode("utf8")).hex()
        return cipher

    def __init__(self, interval: float = 0.01) -> None:
        super().__init__(interval=interval)
        self.user_id = ""
        self.drive_id = ""

        self.token_type = ""  # generally "Bearer"
        self.access_token = ""  # access token added to "Authorization" header
        self.refresh_token = ""  # token used to refresh access token

        self.expire_time = datetime.now(timezone.utc).replace(2020)  # access token expire time

    @property
    def client_id(self) -> str:
        """Get from client id from sign in html page.

        If can't get id from html page, return a default id "25dzX3vbYqktVxyX".
        """
        _client_id = "25dzX3vbYqktVxyX"

        sign_html = self._get_sign_in()
        if not sign_html:
            self.logger.warning("Failed to get client id from html page, use default id.")
        else:
            result = re.findall(r"client_id:[ ]*?['|\"]([a-zA-Z0-9]+?)['|\"]", sign_html)
            if not result:
                self.logger.warning("Failed to find client_id from html page text, use default id.")
            else:
                _client_id = result[0]

        return _client_id

    @property
    def access_token(self) -> str:
        """Getter."""
        return self.__access_token

    @access_token.setter
    def access_token(self, value: str):
        """Setter."""
        self.__access_token = value
        # update header
        if self.token_type:
            self.headers["Authorization"] = self.token_type + " " + self.__access_token

    def _get_login_form_data(self, mini_login_html: str) -> dict:
        """Find login form data from mini_login_html."""

        result = re.findall(
            r"['\"]loginFormData['\"][ ]*?:[ ]*?(\{.+?\})",
            mini_login_html, re.S
        )

        if not result:
            self.logger.error("Failed to find login form data from mini_login_html.")
            return {}

        return json.loads(result[0])

    def _get_pub_n_e(self, mini_login_html: str) -> Tuple[str, str]:
        """Get Modulus and Exponent from html page.

        Returns:
            (n, e)
        """
        result_e = re.findall(
            r"['\"]rsaExponent['\"][ ]*?:[ ]*?['\"]([a-zA-Z0-9]+?)['\"]",
            mini_login_html
        )
        if not result_e:
            self.logger.warning("Failed to find exponent, use default 65537.")
            e = "10001"
        else:
            e = result_e[0]
        result_n = re.findall(
            r"['\"]rsaModulus['\"][ ]*?:[ ]*?['\"]([a-zA-Z0-9]+?)['\"]",
            mini_login_html
        )
        if not result_n:
            self.logger.error("Failed to find Modulus.")
            n = ""
        else:
            n = result_n[0]

        return (n, e)

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

        # check access token valid before caculate
        if not self._check_refresh():
            return ""
        if version == "v1":
            md5_token = hashlib.md5(self.access_token.encode("utf8")).hexdigest()
            start = int(md5_token[0:16], 16) % file_size
            with filepath.open("rb") as f:
                f.seek(start)
                proof_code = b64encode(f.read(8)).decode("utf8")
        else:
            raise ValueError("version must be v1")

        return proof_code

    def _check_refresh(self) -> bool:
        """Check token and try refresh it if is about to expire.

        Used before any api call and access to self.access_token.
        """

        # if expire in 5 min
        if (self.expire_time - datetime.now(timezone.utc)).total_seconds() <= 60:
            self.logger.warning("Token is about to expire, try to auto refresh.")

            # try refresh token
            refresh_info = self._post_token_refresh(self.refresh_token)
            if not refresh_info:
                self.logger.error("Refresh token failed.")
                return False

            # update info
            self.user_id = refresh_info["user_id"]
            self.drive_id = refresh_info["default_drive_id"]

            self.token_type = refresh_info["token_type"]
            self.access_token = refresh_info["access_token"]
            self.refresh_token = refresh_info["refresh_token"]

            self.expire_time = isoparse(refresh_info["expire_time"])  # include timezone, utc time

        return True

    def login(self, usrn: str, pwd: str, *, refresh_token: str = "", cookies: dict = None) -> bool:
        """Login.

        Args:
            usrn (str): Username.
            pwd (str): Password.
        """

        # TODO: usrn and pwd login
        if usrn and pwd:
            raise NotImplementedError

            auth_html = self._get_v2_oauth_authorize(self.client_id)
            mini_login_html = self._get_passport_mini_login()

            login_form_data = self._get_login_form_data(mini_login_html)
            pub_n, pub_e = self._get_pub_n_e(mini_login_html)

            login_info = self._post_passport_newlogin_login(
                usrn,
                self._rsa_encrypt(pwd, pub_n, pub_e),
                False,
            )

        else:
            # refresh token login
            if not refresh_token:
                self.logger.error("Failed to login.")
                return False

            self.refresh_token = refresh_token
            if not self._check_refresh():
                self.logger.error("Failed to get fresh token and login.")
                return False

            # optional add some cookies
            if cookies:
                self.cookies.update(cookies)

            return True

    def logout(self) -> bool:
        # XXX: not really logout
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
            self.logger.info("Check name mode is auto_rename for create folder {}.".format(folder_path.as_posix()))

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
            self.logger.info("Folder {} already exist.".format(folder_path.as_posix()))

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
