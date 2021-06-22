# -*- coding: UTF-8 -*-

from pathlib import Path

import cv2
import numpy as np
from utils import nocaptcha, xsession

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "www.bilibili.com"

    def __init__(self, usrn: str, pwd: str, useproxies=False, log_path=None, cookies: dict = None) -> None:
        super().__init__(usrn, pwd, useproxies=useproxies, log_path=log_path)
        self.s = xsession.Bilibili(self.log_path, cookies=cookies)
        self.s.headers.update(self.headers)
        if useproxies:
            self.s.proxies.update(self.proxies)

    # def _get_validate(self, try_times=10) -> dict:
    #     """
    #     Args:
    #         try_times: times to try validate

    #     Returns:
    #     {
    #         "token": "xxx",
    #         "validate_data": {"validate": "xxx", "seccode": "xxx"} | {"captcha": "xxx"}
    #     }

    #     """
    #     # get captcha info
    #     # do ten times loop to try recognize captcha
    #     captcha_validate_data = {}
    #     for _ in range(try_times):
    #         captcha_validate_data.clear()
    #         captcha_info = self._get_captcha_info()

    #         if captcha_info:
    #             # print(captcha_info)
    #             captcha_type = captcha_info.get("type")
    #             # TODO: recognize different types of geetest captcha

    #             if captcha_type == "img":
    #                 captcha_img = self._get_captcha_img(captcha_info.get("token"))

    #                 # cache captcha image
    #                 Path("./tmp/cache.jpg").write_bytes(captcha_img)

    #                 # trans to cv image format
    #                 captcha_img = cv2.imdecode(
    #                     np.array(bytearray(captcha_img), dtype="uint8"),
    #                     cv2.IMREAD_GRAYSCALE
    #                 )

    #                 # try recognize img captcha
    #                 captcha_validate = nocaptcha.img_recognize(captcha_img)
    #                 if captcha_validate:
    #                     captcha_validate_data["captcha"] = captcha_validate
    #                     break

    #             elif captcha_type == "geetest":
    #                 gt = captcha_info.get("geetest").get("gt")
    #                 challenge = captcha_info.get("geetest").get("challenge")

    #                 raise NotImplementedError("Geetest Captcha")

    #                 captcha_validate = nogeetest.get_validate(gt, challenge)
    #                 if captcha_validate:
    #                     captcha_validate_data["validate"] = captcha_validate
    #                     captcha_validate_data["seccode"] = captcha_validate + "|jordan"
    #                     break
    #             else:
    #                 raise NotImplementedError("Unknown Captcha type.")
    #     if not captcha_validate_data:
    #         return {}

    #     captcha_data = {
    #         "token": captcha_info.get("token"),
    #         "validate_data": captcha_validate_data
    #     }
    #     return captcha_data

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

        raise NotImplementedError

    def _signin(self) -> bool:
        # get last coin count
        nav_info = self.s.get_web_nav()
        if not nav_info:
            return False
        last_money_count = nav_info.get("money")

        # get latest coin count
        nav_info = self.s.get_web_nav()
        if not nav_info:
            return False
        latest_coin_count = nav_info.get("money")

        # if sign in successfully, coin++
        if latest_coin_count <= last_money_count:
            return False
        return True

    def _logout(self) -> bool:
        if not self.usrn or not self.pwd:
            return True

        ret = self.s.post_logout()
        # print(res.text)
        # print(res.cookies)
        if not ret:
            return False
        return True
