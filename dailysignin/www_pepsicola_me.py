# -*- coding: UTF-8 -*-

from datetime import datetime, timedelta, timezone
from time import sleep

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "www.pepsicola.me"
    url_index = f"https://{site_name}/index.php"
    url_login = f"https://{site_name}/api/v1/passport/auth/login"
    url_order = f"https://{site_name}/api/v1/user/order/save"
    url_checkout = f"https://{site_name}/api/v1/user/order/checkout"
    url_info = f"https://{site_name}/api/v1/user/info"
    url_logout = f"https://{site_name}/api/v1/user/logout"

    def __init__(self, usrn: str, pwd: str, useproxies=False) -> None:
        super().__init__(usrn, pwd, useproxies)
        self.s.get(self.url_index)

    def _login(self) -> bool:
        res = self.s.post(
            self.url_login,
            data={"email": self.usrn, "password": self.pwd}
        )
        if res.status_code != 200:
            return False
        return True

    def _renew(self) -> bool:
        """"""
        res = self.s.post(
            self.url_order,
            data={"period": "month_price", "plan_id": 7}
        )
        if res.status_code != 200:
            return False

        order_num = res.json()["data"]
        res = self.s.post(
            self.url_checkout,
            data={"trade_no": order_num, "method": 4}
        )
        if res.status_code != 200:
            return False

        if not res.json()["data"]:
            return False
        return True

    def _reset(self) -> bool:
        """"""
        res = self.s.post(
            self.url_order,
            data={"period": "reset_price", "plan_id": 7}
        )
        if res.status_code != 200:
            return False

        order_num = res.json()["data"]
        res = self.s.post(
            self.url_checkout,
            data={"trade_no": order_num, "method": 4}
        )

        if res.status_code != 200:
            return False

        if not res.json()["data"]:
            return False
        return True

    def _signin(self) -> bool:
        ret = True
        ret = self._reset() and ret

        res = self.s.get(self.url_info)
        if res.status_code != 200:
            return False

        expire_time = res.json()["data"]["expired_at"]
        expire_time = datetime.fromtimestamp(expire_time, timezone(timedelta(hours=8)))
        left_time = expire_time - datetime.now(timezone(timedelta(hours=8)))
        sleep(3)
        if left_time.days < 60:
            ret = self._renew() and ret

        return ret

    def _logout(self) -> bool:
        res = self.s.get(self.url_logout)
        if res.status_code != 200:
            return False
        return True
