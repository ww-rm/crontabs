# -*- coding: UTF-8 -*-

import imghdr
import json
from base64 import b64encode
from os import PathLike
from pathlib import Path
from typing import Iterator, List

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from .base import XSession, empty_retry


class BilibiliBase(XSession):
    """Base api wrapper of bilibili, don't use it directly."""

    url_host = "https://www.bilibili.com/"

    dynamic_svr_create = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create"
    dynamic_svr_create_draw = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_draw"
    dynamic_svr_rm_dynamic = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/rm_dynamic"
    dynamic_svr_get_dynamic_detail = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail"  # ?dynamic_id=539112416787513871"

    drawImage_upload = "https://api.vc.bilibili.com/api/v1/drawImage/upload"
    cover_up = "https://member.bilibili.com/x/vu/web/cover/up"

    web_interface_nav = "https://api.bilibili.com/x/web-interface/nav"

    web_login = "https://passport.bilibili.com/x/passport-login/web/login"
    login_exit = "https://passport.bilibili.com/login/exit/v2"

    passport_login_captcha = "https://passport.bilibili.com/x/passport-login/captcha"  # ?source=main_web"
    recaptcha_img = "https://api.bilibili.com/x/recaptcha/img"  # ?t=0.46679774852401557&token=7d57eb2167964b25af75aa15d8488a46"
    web_key = "https://passport.bilibili.com/x/passport-login/web/key"  # ?r=0.4811057511950463"

    @property
    def csrf_token(self) -> str:
        return self.cookies.get("bili_jct", default="")

    def _check_response(self, res: requests.Response) -> dict:
        """Check the status code and error code of a json response, and return data of body

        Args:
            res (Response): response to check

        Returns:
            data (json): empty dict or data dict, if empty, will log error info    
        """

        if res.status_code != 200:
            return {}
        elif res.json()["code"] != 0:
            self.logger.error("{}:{}:{}".format(res.url, res.json()["code"], res.json()["message"]))
            return {}
        return res.json()["data"]

    def _get_web_key(self, r=0.4811057511950463) -> dict:
        """Get web key
        """
        res = self.get(
            BilibiliBase.web_key,
            params={"r": r}
        )
        return self._check_response(res)

    @empty_retry()
    def _post_draw_image_upload(self, img_path: PathLike) -> dict:
        """Upload a image and get url on static server.

        Args:
            image_path: local image file path

        Returns:
            see responses folder
        """
        img_path = Path(img_path)
        with img_path.open("rb") as f:
            res = self.post(
                BilibiliBase.drawImage_upload,
                files={
                    "file_up": (img_path.name, f, "image/{}".format(imghdr.what(f))),
                    "biz": (None, "draw"),
                    "category": (None, "daily")
                }
            )

        return self._check_response(res)

    def _post_cover_up(self, cover: str) -> dict:
        """Upload a image cover and get url on static server

        Args:
            cover: image in html data url format, should be 16:10 (width: height)

        Returns:
            see responses folder
        """
        res = self.post(
            BilibiliBase.cover_up,
            data={"cover": cover, "csrf": self.csrf_token}
        )
        return self._check_response(res)

    def _get_web_nav(self) -> dict:
        """
        Returns:
            see responses folder
        """

        res = self.get(BilibiliBase.web_interface_nav)
        return self._check_response(res)

    def _get_dynamic_detail(self, dynamic_id: str) -> dict:
        """Get details of a dynamic.

        Note:
            if dynamic ever exist, "data" will be returned correctly, but no result, only has "_gt_" field,

            if dynamic exist and being auditing, will has `extra` field in `data.card` and `data.card.extra.is_auditing` == `1`
        """
        res = self.get(
            BilibiliBase.dynamic_svr_get_dynamic_detail,
            params={"dynamic_id": dynamic_id}
        )
        return self._check_response(res)

    def _post_create(
        self, content: str,
        *,
        dynamic_id=0, type_=4, rid=0,
        up_choose_comment=0, up_close_comment=0,
        at_uids="", extension=None, ctrl=None
    ) -> dict:
        """Create a text only dynamic.

        Args:
            content: content for the dynamic
            at_uids: "xxx,xxx"
            ctrl: "[{"location":0,"type":1,"length":7,"data":"xxx"},{"location":7,"type":1,"length":7,"data":"xxx"}]"
        """
        res = self.post(
            BilibiliBase.dynamic_svr_create,
            data={
                "content": content,
                "up_choose_comment": up_choose_comment,
                "up_close_comment": up_close_comment,
                "dynamic_id": dynamic_id,
                "type": type_,
                "rid": rid,
                "at_uids": at_uids,
                "ctrl": json.dumps([]),
                "extension": json.dumps({
                    "emoji_type": 1,
                    "from": {"emoji_type": 1},
                    "flag_cfg": {}
                }),
                "csrf": self.csrf_token,
                "csrf_token": self.csrf_token
            }
        )

        return self._check_response(res)

    def _post_create_draw(
        self, content: str, pictures: list,
        description: str = "", title: str = "", tags: str = "",
        *,
        at_uids="", at_control=None,
        biz=3, category=3, type_=0,
        from_="create.dynamic.web",
        up_choose_comment=0, up_close_comment=0,
        extension=None, setting=None
    ) -> dict:
        """Create dynamic with pictures.

        Args:
            content: text content
            pictures: list of json object gotten from self._post_draw_image_upload
            title: unknown
            description: unknown
            tags: unknown
        """

        res = self.post(
            BilibiliBase.dynamic_svr_create_draw,
            data={
                "content": content,
                "pictures": json.dumps(pictures),
                "title": title,
                "description": description or content,
                "category": category,
                "tags": tags,
                "up_choose_comment": up_choose_comment,
                "up_close_comment": up_close_comment,
                "biz": biz,
                "type": type_,
                "from": from_,
                "at_uids": at_uids,
                "at_control": json.dumps([]),
                "setting": json.dumps({
                    "copy_forbidden": 0,
                    "cachedTime": 0
                }),
                "extension": json.dumps({
                    "emoji_type": 1,
                    "from": {"emoji_type": 1},
                    "flag_cfg": {}
                }),
                "csrf": self.csrf_token,
                "csrf_token": self.csrf_token
            }
        )
        # print(res.text)
        return self._check_response(res)

    def _post_rm_dynamic(self, dynamic_id: str) -> dict:
        """Delete a dynamic"""
        res = self.post(
            BilibiliBase.dynamic_svr_rm_dynamic,
            data={
                "dynamic_id": dynamic_id,
                "csrf": self.csrf_token,
                "csrf_token": self.csrf_token
            }
        )
        return self._check_response(res)

    def _get_login_captcha(self, source: str = "main_web") -> dict:
        """
        Returns:
            see responses folder
        """
        res = self.get(
            BilibiliBase.passport_login_captcha,
            params={"source": source}
        )
        return self._check_response(res)

    def _get_recaptcha_img(self, token: str, chunk_size: int = 10485760) -> Iterator[bytes]:
        """Get simple image captcha."""
        res = self.get(
            BilibiliBase.recaptcha_img,
            params={"token": token},
            stream=True
        )

        if res.status_code != 200:
            return b""  # Need to make bool False
        return res.iter_content(chunk_size)

    def _post_login(
        self, username: str, password: str, token_info: dict, validate_data: str,
        source="main_web", keep="false", go_url=""
    ) -> dict:
        """Login

        Args:
            username (str): username
            password (str): password with salt, and use rsa encrypted.
            token_info (dict): returned from self.get_login_captcha
            validate_data (str): string get from geetest or image recognition
        """

        login_data = {
            "source": source,
            "username": username,
            "password": password,
            "keep": keep,
            "token": token_info["token"],
            "go_url": go_url
        }

        token_type = token_info["type"]
        if token_type == "img":
            login_data["captcha"] = validate_data
        elif token_type == "geetest":
            login_data["validate"] = validate_data
            login_data["seccode"] = validate_data + "|jordan"
        else:
            raise ValueError("Unknown captcha type.")

        res = self.post(BilibiliBase.web_login, data=login_data)
        return self._check_response(res)

    def _post_logout(self) -> bool:
        res = self.post(
            BilibiliBase.login_exit,
            data={
                "biliCSRF": self.csrf_token,
                "gourl": ""
            }
        )
        # NOTE: if no login info to logout, res will be html format, otherwise be json data
        if res.status_code != 200:
            return False
        try:
            return (res.json()["code"] == 0)
        except ValueError:
            return False


class Bilibili(BilibiliBase):
    """Api for bilibili."""

    @staticmethod
    def _rsa_encrypt(plain: str, public_key: str) -> str:
        key = RSA.import_key(public_key)
        encrypter = PKCS1_v1_5.new(key)

        cipher = encrypter.encrypt(plain.encode("utf8"))
        cipher = b64encode(cipher).decode("utf8")
        return cipher

    def login(self, usrn: str, pwd: str, *, cookies: dict = None) -> bool:
        """Login.

        Args:
            usrn: username
            pwd:  password
        """
        # username password login
        if usrn and pwd:
            raise NotImplementedError

            # get pubkey and hash
            rsa_pubkey = self._get_web_key()
            if not rsa_pubkey:
                self.logger.error("Failed to get pubkey.")
                return False

            pwd = self._rsa_encrypt(rsa_pubkey["hash"]+pwd, rsa_pubkey["key"])

            token_info = self._get_login_captcha()
            if not token_info:
                self.logger.error("Failed to get login captcha.")
                return False

            # TODO: automatically get validate_data
            token_type = token_info["type"]
            if token_type == "img":
                img_data = self._get_recaptcha_img(token_info["token"])
                # TODO: recognize img
                raise NotImplementedError
            elif token_type == "geetest":
                # TODO: get geetest validate data
                raise NotImplementedError
            else:
                raise ValueError("Unknown captcha type.")

            login_info = self._post_login(
                usrn, pwd,
                token_info, validate_data
            )

            if not login_info:
                self.logger.error("Failed to login.")
                return False
            return True

        # cookies login
        else:
            if not cookies:
                return False
            self.cookies.update(cookies)
            return True

    def logout(self) -> bool:
        """Logout."""

        ret = self._post_logout()
        if not ret:
            return False
        return True

    def create_dynamic(self, content: str, pictures: List[PathLike] = None) -> dict:
        """Create a dynamic with or without pictures.

        Args:

        Returns:

        """
        # dynamic without pictures
        if not pictures:
            create_info = self._post_create(content)
            if not create_info:
                self.logger.error("Failed to create dynamic.")
                return {}
            return create_info

        # dynamic with pictures
        else:
            # remain first 9 pictures
            if len(pictures) > 9:
                self.logger.warning("Number of pictures more than 9, only keep first 9 pictures.")
                pictures = pictures[:9]

            # upload pictures
            res_pics = []
            for pic_path in map(Path, pictures):
                pic_info = self._post_draw_image_upload(pic_path)
                if pic_info:
                    res_pics.append({
                        "img_src": pic_info["image_url"],
                        "img_width": pic_info["image_width"],
                        "img_height": pic_info["image_height"],
                        "img_size": pic_path.stat().st_size / 1024
                    })

            create_info = self._post_create_draw(content, res_pics)
            if not create_info:
                self.logger.error("Failed to create dynamic.")
                return {}
            return create_info

    def delete_dynamic(self, dynamic_id: str) -> dict:
        """Delete a dynamic."""

        delete_info = self._post_rm_dynamic(dynamic_id)

        if not delete_info:
            self.logger.error("Failed to delete dynamic {}.".format(dynamic_id))
            return {}
        return delete_info

    def get_dynamic_detail(self, dynamic_id: str) -> dict:
        """Get detail info of a dynamic."""

        detail_info = self._get_dynamic_detail(dynamic_id)
        if not detail_info:
            self.logger.error("Failed to get detail of dynamic {}.".format(dynamic_id))
            return {}
        return detail_info
