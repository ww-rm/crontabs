# -*- coding: UTF-8 -*-

import imghdr
import json
from base64 import b64encode
from pathlib import Path
from typing import List, Union

import bs4
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from .base import XSession, empty_retry


class Bilibili(XSession):
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

    @staticmethod
    def _rsa_encrypt(plain: str, public_key: str):
        key = RSA.import_key(public_key)
        encrypter = PKCS1_v1_5.new(key)

        cipher = encrypter.encrypt(plain.encode("utf8"))
        cipher = b64encode(cipher).decode("utf8")
        return cipher

    def __init__(self, interval: float = 0.01, cookies: dict = None) -> None:
        super().__init__(interval=interval)
        if cookies:
            for name, value in cookies.items():
                self.cookies.set(name, value, domain="bilibili.com", path="/")
        # print(cookies)

    def _get_csrf(self) -> str:
        return self.cookies.get("bili_jct", default="")

    def _get_web_key(self, r=0.4811057511950463):
        """Get web key
        """
        res = self.get(
            self.web_key,
            params={"r": r}
        )
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    @empty_retry()
    def _post_upload(self, img_path: Union[str, Path]) -> dict:
        """Upload a image and get url on static server

        Args:
            image_path: local image file path

        Returns:
            see responses folder
        """
        img_path = Path(img_path)
        with img_path.open("rb") as f:
            res = self.post(
                self.drawImage_upload,
                files={
                    "file_up": (img_path.name, f, "image/{}".format(imghdr.what(f))),
                    "biz": (None, "draw"),
                    "category": (None, "daily")
                }
            )

        if res.status_code != 200:
            self.logger.warning("Bilibili:Failded to Upload file {}:{}".format(Path(img_path).name, res.status_code))
            return {}
        elif res.json()["code"] != 0:
            self.logger.warning("Bilibili:Failded to Upload file {}:{}".format(Path(img_path).name, res.json()["message"]))
            return {}
        return res.json()["data"]

    def _post_cover_up(self, cover: str) -> dict:
        """Upload a image cover and get url on static server

        Args

        cover:
            image in html data url format, should be 16:10 (width: height)

        Returns

        see responses folder
        """
        res = self.post(
            self.cover_up,
            data={"cover": cover, "csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def get_web_nav(self) -> dict:
        """
        Returns

        see responses folder
        """

        res = self.get(self.web_interface_nav)
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def get_dynamic_detail(self, dynamic_id) -> dict:
        """Get details of a dynamic

        Note

        if dynamic ever exist, "data" will be returned correctly, but no result, only has "_gt_" field,

        if dynamic exist and being auditing, will has `extra` field in `data.card` and `data.card.extra.is_auditing` == `1`
        """
        res = self.get(self.dynamic_svr_get_dynamic_detail, params={"dynamic_id": dynamic_id})
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def post_create(self, content: str,
                    dynamic_id=0, type_=4, rid=0,
                    up_choose_comment=0, up_close_comment=0,
                    at_uids="", extension=None, ctrl=None) -> dict:
        """Create a dynamic

        Args:
            content: content for the dynamic
            at_uids: "xxx,xxx"
            ctrl: "[{"location":0,"type":1,"length":7,"data":"xxx"},{"location":7,"type":1,"length":7,"data":"xxx"}]"
        """
        res = self.post(
            self.dynamic_svr_create,
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
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            })

        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def post_create_draw(self, content: str, pictures: List[Union[str, Path]],
                         description: str = "", title: str = "", tags: str = "",
                         at_uids="", at_control=None,
                         biz=3, category=3, type_=0,
                         from_="create.dynamic.web",
                         up_choose_comment=0, up_close_comment=0,
                         extension=None, setting=None):
        """Create dynamic with pictures

        Args:
            content: main content
            pictures: local paths of pictures needed to create with dynamic
            title: unknown
            description: unknown
            tags: unknown
        """
        res_pics = []
        # upload pictures
        for pic_path in map(Path, pictures):
            pic_info = self._post_upload(pic_path)
            if pic_info:
                res_pics.append({
                    "img_src": pic_info["image_url"],
                    "img_width": pic_info["image_width"],
                    "img_height": pic_info["image_height"],
                    "img_size": pic_path.stat().st_size / 1024
                })

        res = self.post(
            self.dynamic_svr_create_draw,
            data={
                "content": content,
                "pictures": json.dumps(res_pics),
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
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            }
        )
        # print(res.text)
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def post_rm_dynamic(self, dynamic_id) -> dict:
        """Delete a dynamic"""
        res = self.post(
            self.dynamic_svr_rm_dynamic,
            data={
                "dynamic_id": dynamic_id,
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            }
        )
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        else:
            return res.json()["data"]

    def get_login_captcha(self, source="main_web") -> dict:
        """
        Returns:

        see responses folder
        """
        res = self.get(
            self.passport_login_captcha,
            params={"source": source}
        )
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def get_recaptcha_img(self, token: str) -> bytes:
        """Get simple image captcha"""
        res = self.get(
            self.recaptcha_img,
            params={"token": token}
        )

        if res.status_code != 200:
            return b""
        return res.content

    def post_login(self, username: str, password: str, token_info: dict, validate_data: str,
                   source="main_web", keep="false", go_url="") -> dict:
        """Login

        Args:
            username: 
                username
            password: 
                password
            token: 
                returned from self.get_login_captcha
            validate_data: 
                string get from geetest or image recognition
        """
        # get pubkey and hash
        rsa_pubkey = self._get_web_key()
        if not rsa_pubkey:
            return {}

        login_data = {
            "source": source,
            "username": username,
            "password": self._rsa_encrypt(rsa_pubkey["hash"]+password, rsa_pubkey["key"]),
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

        res = self.post(self.web_login, data=login_data)
        if res.status_code != 200 or res.json()["code"] != 0:
            return {}
        return res.json()["data"]

    def post_logout(self) -> bool:
        res = self.post(
            self.login_exit,
            data={
                "biliCSRF": self._get_csrf(),
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
