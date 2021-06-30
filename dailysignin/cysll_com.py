# -*- coding: UTF-8 -*-

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "cysll.com"
    url_login = "https://cysll.com/wp-json/jwt-auth/v1/token"
    url_signin = "https://cysll.com/wp-json/b2/v1/userMission"
    url_logout = "https://cysll.com/wp-json/b2/v1/loginOut"

    def _login(self) -> bool:
        res = self.s.post(
            self.url_login,
            data={
                "nickname": "",
                "username": self.usrn,
                "password": self.pwd,
                "code": "",
                "img_code": "",
                "invitation_code": "",
                "token": "",
                "smsToken": "",
                "luoToken": "",
                "confirmPassword": "",
                "loginType": ""
            }
        )
        if res.status_code != 200:
            return False

        # add Authorization header
        self.s.headers["Authorization"] = "Bearer " + res.json()["token"]
        return True

    def _signin(self) -> bool:
        res = self.s.post(self.url_signin)
        if res.status_code != 200:
            return False
        return True

    def _logout(self) -> bool:
        res = self.s.get(self.url_logout)
        if res.status_code != 200:
            return False
        return True
