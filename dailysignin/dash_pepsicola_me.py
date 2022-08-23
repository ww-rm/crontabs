# -*- coding: UTF-8 -*-

import re
from datetime import datetime, timedelta, timezone
from time import sleep

from bs4 import BeautifulSoup

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "dash.pepsicola.me"
    url_index = f"https://{site_name}/index.php"
    url_login = f"https://{site_name}/auth/login"
    url_user = f"https://{site_name}/user"
    url_buy = f"https://{site_name}/user/buy"
    url_buy_traffic_package = f"https://{site_name}/user/buy_traffic_package"
    url_logout = f"https://{site_name}/user/logout"

    def __init__(self, usrn: str, pwd: str, useproxies=False) -> None:
        super().__init__(usrn, pwd, useproxies)
        self.s.get(self.url_index)

    def _login(self) -> bool:
        res = self.s.post(
            self.url_login,
            data={"email": self.usrn, "passwd": self.pwd, "code": ""}
        )
        if res.status_code != 200:
            return False
        return True

    def _get_user_info(self) -> dict:
        """"""
        res = self.s.get(self.url_user)
        if res.status_code != 200:
            return {}

        day_left = re.search(r"(\d{4}-\d{2}-\d{2}) 到期", res.text)
        day_left = day_left.group(1) if day_left else "2000-01-01"
        day_left = datetime.strptime(day_left, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=8)))

        traffic_left = re.search(r"(\d*?(\.\d*?)?)GB", res.text)
        traffic_left = float(traffic_left.group(1)) if traffic_left else 0

        info = {
            "day_left": day_left,
            "traffic_left": traffic_left
        }

        return info

    def _buy(self) -> bool:
        """"""
        res = self.s.post(
            self.url_buy,
            data={"coupon": "", "shop": "1", "autorenew": "0", "disableothers": "1"}
        )
        if res.status_code != 200:
            return False

        try:
            if res.json()["ret"] != 1:
                return False
        except (ValueError, KeyError):
            return False
        return True

    def _buy_traffic_packge(self) -> bool:
        """"""
        res = self.s.post(
            self.url_buy_traffic_package,
            data={"shop": "3"}
        )
        if res.status_code != 200:
            return False

        try:
            if res.json()["ret"] != 1:
                return False
        except (ValueError, KeyError):
            return False
        return True

    def _signin(self) -> bool:
        user_info = self._get_user_info()
        if not user_info:
            return False

        if (user_info["day_left"] - datetime.now(timezone(timedelta(hours=8)))).days < 90:
            if not self._buy():
                return False
            for _ in range(20):
                self._buy_traffic_packge()
                sleep(1)
        else:
            for _ in range(20 - int(user_info["traffic_left"] / 5)):
                self._buy_traffic_packge()
                sleep(1)
        return True

    def _logout(self) -> bool:
        res = self.s.get(self.url_logout)
        if res.status_code != 200:
            return False
        return True
