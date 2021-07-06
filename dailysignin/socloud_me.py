# -*- coding: UTF-8 -*-

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "socloud.me"
    url_login = "https://socloud.me/auth/login"
    url_signin = "https://socloud.me/user/checkin"
    url_logout = "https://socloud.me/user/logout"

    def _login(self) -> bool:
        res = self.s.post(
            self.url_login,
            data={"email": self.usrn, "passwd": self.pwd, "code": ""}
        )
        if res.status_code != 200 or res.json()["ret"] != 1:
            return False
        return True

    def _signin(self) -> bool:
        res = self.s.post(self.url_signin)
        if res.status_code != 200 or res.json()["ret"] != 1:
            return False
        return True

    def _logout(self) -> bool:
        res = self.s.get(self.url_logout)
        if res.status_code != 200:
            return False
        return True
