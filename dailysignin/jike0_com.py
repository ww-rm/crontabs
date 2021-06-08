# -*- coding: UTF-8 -*-

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "jike0.com"
    url_login = "https://jike0.com/auth/login"
    url_signin = "https://jike0.com/user/checkin"
    url_logout = "https://jike0.com/user/logout"

    def _login(self) -> bool:
        res = self.s.post(
            self.url_login,
            data={"email": self.usrn, "passwd": self.pwd, "code": ""}
        )
        if res.status_code != 200 or res.json().get("ret") != 1:
            return False
        return True

    def _signin(self) -> bool:
        res = self.s.post(self.url_signin)
        if res.status_code != 200 or res.json().get("ret") != 1:
            return False
        return True

    def _logout(self) -> bool:
        res = self.s.get(self.url_logout)
        if res.status_code != 200:
            return False
        return True
