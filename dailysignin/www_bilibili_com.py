# -*- coding: UTF-8 -*-

from base64 import b64encode
from pathlib import Path

import cv2
import numpy as np
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from utils import nocaptcha, nogeetest

from .base import BaseSigner


def _rsa_encrypt(plain: str, public_key: str) -> str:
    key = RSA.import_key(public_key)
    encrypter = PKCS1_v1_5.new(key)

    cipher = encrypter.encrypt(plain.encode("utf8"))
    cipher = b64encode(cipher).decode("utf8")
    return cipher


class Signer(BaseSigner):
    site_name = "www.bilibili.com"
    url_login = "https://passport.bilibili.com/x/passport-login/web/login"
    url_signin = "https://api.bilibili.com/x/web-interface/nav"
    url_logout = "https://passport.bilibili.com/login/exit/v2"

    url_captcha_info = "https://passport.bilibili.com/x/passport-login/captcha"  # ?source=main_web"
    url_captcha_img = "https://api.bilibili.com/x/recaptcha/img"  # ?t=0.46679774852401557&token=7d57eb2167964b25af75aa15d8488a46"
    url_pubkey = "https://passport.bilibili.com/x/passport-login/web/key"  # ?r=0.4811057511950463"

    def __init__(self, usrn: str, pwd: str, cookies: dict = None, useproxies=False, log_path=None) -> None:
        super().__init__(usrn, pwd, useproxies=useproxies, log_path=log_path)
        if cookies:
            self.s.cookies.update(cookies)

    def _get_captcha_info(self) -> dict:
        """
        response body

        {
            "code": 0, "message": "0", "ttl": 1,
            "data": {
                "type": "img",
                "token": "54b8c7a7633340adb65522bb46697a2f",
                "geetest": {"challenge": "", "gt": ""}, "tencent": {"appid": ""}
            }
        }
        """
        res = self.s.get(
            self.url_captcha_info,
            # params={"source": "main_web"}
        )
        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        return res.json().get("data")

    def _get_captcha_img(self, token) -> bytes:
        res = self.s.get(
            self.url_captcha_img,
            params={"token": token}
        )

        if res.status_code != 200:
            return b""
        return res.content

    def _get_pubkey(self) -> dict:
        """
        response body

        {
            "code": 0, "message": "0", "ttl": 1,
            "data": {
                "hash": "7a0d46c0d85b6e0f",
                "key": "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDjb4V7EidX/ym28t2ybo0U6t0n\n6p4ej8VjqKHg100va6jkNbNTrLQqMCQCAYtXMXXp2Fwkk6WR+12N9zknLjf+C9sx\n/+l48mjUU8RqahiFD1XT/u2e0m2EN029OhCgkHx3Fc/KlFSIbak93EH/XlYis0w+\nXl69GV6klzgxW6d2xQIDAQAB\n-----END PUBLIC KEY-----\n"
            }
        }
        """
        res = self.s.get(
            self.url_pubkey,
            # params={"r": 0.4811057511950463}
        )
        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        return res.json().get("data")

    def _get_csrf(self) -> str:
        return self.s.cookies.get("bili_jct", default="")

    def _get_validate(self, try_times=10) -> dict:
        """
        Args:
            try_times: times to try validate

        Returns:
        {
            "token": "xxx",
            "validate_data": {"validate": "xxx", "seccode": "xxx"} | {"captcha": "xxx"}
        }

        """
        # get captcha info
        # do ten times loop to try recognize captcha
        captcha_validate_data = {}
        for _ in range(try_times):
            captcha_validate_data.clear()
            captcha_info = self._get_captcha_info()

            if captcha_info:
                # print(captcha_info)
                captcha_type = captcha_info.get("type")
                # TODO: recognize different types of geetest captcha

                if captcha_type == "img":
                    captcha_img = self._get_captcha_img(captcha_info.get("token"))

                    # cache captcha image
                    Path("./tmp/cache.jpg").write_bytes(captcha_img)

                    # trans to cv image format
                    captcha_img = cv2.imdecode(
                        np.array(bytearray(captcha_img), dtype="uint8"),
                        cv2.IMREAD_GRAYSCALE
                    )

                    # try recognize img captcha
                    captcha_validate = nocaptcha.img_recognize(captcha_img)
                    if captcha_validate:
                        captcha_validate_data["captcha"] = captcha_validate
                        break

                elif captcha_type == "geetest":
                    gt = captcha_info.get("geetest").get("gt")
                    challenge = captcha_info.get("geetest").get("challenge")

                    raise NotImplementedError("Geetest Captcha")
                    
                    captcha_validate = nogeetest.get_validate(gt, challenge)
                    if captcha_validate:
                        captcha_validate_data["validate"] = captcha_validate
                        captcha_validate_data["seccode"] = captcha_validate + "|jordan"
                        break
                else:
                    raise NotImplementedError("Unknown Captcha type.")
        if not captcha_validate_data:
            return {}

        captcha_data = {
            "token": captcha_info.get("token"),
            "validate_data": captcha_validate_data
        }
        return captcha_data

    def _login(self) -> bool:
        """
        1. Get captcha
        2. Recognize captcha
        3. Get pubkey
        4. login
        """

        # if use cookies to login
        if ("bili_jct" in self.s.cookies
            and "SESSDATA" in self.s.cookies
                and "DedeUserID" in self.s.cookies):
            return True

        # get validate data
        captcha_data = self._get_validate()
        if not captcha_data:
            return False

        # get pubkey and hash
        rsa_pubkey = self._get_pubkey()
        if not rsa_pubkey:
            return False

        login_data = {
            "source": "main_web",
            "username": self.usrn,
            "password": _rsa_encrypt(rsa_pubkey.get("hash")+self.pwd, rsa_pubkey.get("key")),
            "keep": "false",
            "token": captcha_data.get("token"),
            "go_url": ""
        }
        login_data.update(captcha_data.get("validate_data"))

        res = self.s.post(self.url_login, data=login_data)
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        return True

    def _signin(self) -> bool:
        # get last coin count
        res = self.s.get(self.url_signin)
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        last_money_count = res.json().get("data").get("money")

        # get latest coin count
        res = self.s.get(self.url_signin)
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        latest_coin_count = res.json().get("data").get("money")

        # if sign in successfully, coin++
        if latest_coin_count <= last_money_count:
            return False
        return True

    def _logout(self) -> bool:
        res = self.s.post(
            self.url_logout,
            data={
                "biliCSRF": self._get_csrf(),
                "gourl": ""
            }
        )
        print(res.text)
        print(res.cookies)
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        return True
