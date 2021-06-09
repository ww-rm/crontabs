# -*- coding: UTF-8 -*-

from base64 import b64encode
from pathlib import Path

import cv2
import numpy as np
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from .base import BaseSigner


def _img_captcha(img: np.ndarray) -> str:
    cv2.imwrite("./captcha.jpg", img)
    code = input("Enter Captcha: ").lower()
    return code


def _rsa_encrypt(plain: str, public_key: str) -> str:
    key = RSA.import_key(public_key)
    encrypter = PKCS1_v1_5.new(key)

    cipher = encrypter.encrypt(plain.encode("utf8"))
    cipher = b64encode(cipher).decode("utf8")
    return cipher


class Signer(BaseSigner):
    site_name = "www.bilibili.com"
    url_login = "https://passport.bilibili.com/x/passport-login/web/login"
    # url_signin = "https://jike0.com/user/checkin"
    url_logout = "https://passport.bilibili.com/login/exit/v2"

    url_sid = "https://passport.bilibili.com/qrcode/getLoginUrl"
    url_captcha_info = "https://passport.bilibili.com/x/passport-login/captcha"  # ?source=main_web"
    url_captcha_img = "https://api.bilibili.com/x/recaptcha/img"  # ?t=0.46679774852401557&token=7d57eb2167964b25af75aa15d8488a46"
    url_pubkey = "https://passport.bilibili.com/x/passport-login/web/key"  # ?r=0.4811057511950463"

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
        return ""

    def _login(self) -> bool:
        """
        1. Get captcha
        2. Recognize captcha
        3. Get pubkey
        4. login
        """

        # get captcha info
        captcha_info = self._get_captcha_info()
        if captcha_info:
            if captcha_info.get("type") == "img":
                captcha_img = self._get_captcha_img(captcha_info.get("token"))
            else:
                raise NotImplementedError
        else:
            return False

        # cache captcha image and trans to cv image format
        Path("./cache.jpg").write_bytes(captcha_img)
        captcha_img = cv2.imdecode(
            np.array(bytearray(captcha_img), dtype="uint8"),
            cv2.IMREAD_GRAYSCALE
        )

        # TODO: recognize different types of captcha

        # get pubkey and hash
        rsa_pubkey = self._get_pubkey()
        if not rsa_pubkey:
            return False

        res = self.s.post(
            self.url_login,
            data={
                "source": "main_web",
                "username": self.usrn,
                "password": _rsa_encrypt(rsa_pubkey.get("hash")+self.pwd, rsa_pubkey.get("key")),
                "keep": "false",
                "token": captcha_info.get("token"),
                "go_url": "",
                "captcha": _img_captcha(captcha_img)
            }
        )
        print(res.text)
        print(res.cookies)
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        return True

    def _signin(self) -> bool:
        # res = self.s.post(self.url_signin)
        # if res.status_code != 200:
        #     return False
        return True

    def _logout(self) -> bool:
        res = self.s.post(
            self.url_logout,
            data={
                "biliCSRF": self._get_csrf(),
                "gourl": "https://www.bilibili.com/"
            }
        )
        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        return True
