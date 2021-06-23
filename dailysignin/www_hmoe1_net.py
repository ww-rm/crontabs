# -*- coding: UTF-8 -*-

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "www.hmoe1.net"
    url_admin = "https://www.hmoe1.net/wp-admin/admin-ajax.php"

    def __init__(self, usrn: str, pwd: str, useproxies=False) -> None:
        super().__init__(usrn, pwd, useproxies=useproxies)
        self.s.headers["Referer"] = "https://www.hmoe1.net/"

    def _get_nonce(self) -> str:
        res = self.s.get(
            self.url_admin,
            params={
                "action": "285d6af5ed069e78e04b2d054182dcb5"
            }
        )

        if res.status_code != 200:
            return ""

        nonce = res.json().get("_nonce")
        return nonce

    def _login(self) -> bool:
        res = self.s.post(
            self.url_admin,
            params={
                "_nonce": self._get_nonce(),
                "action": "0ac2206cd584f32fba03df08b4123264",
                "type": "login"
            },
            files={
                "email": (None, self.usrn),
                "pwd": (None, self.pwd),
                "type": (None, "login")
            }
        )

        if res.status_code != 200 or res.json().get("code") != 0:
            return False
        return True

    def _signin(self) -> bool:
        res = self.s.get(
            self.url_admin,
            params={
                "_nonce": self._get_nonce(),
                "action": "9f9fa05823795c1c74e8c27e8d5e6930",
                "type": "goSign"
            }
        )
        if res.status_code != 200:
            return False
        return True

    def _logout(self) -> bool:
        res = self.s.get(
            self.url_admin,
            params={
                "action": "e6986f0c2322e89f0b93500144425f88",
                "redirectUrl": "https://www.hmoe1.net/"
            }
        )

        if not res.ok:
            return False
        return True
