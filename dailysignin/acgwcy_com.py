# -*- coding: UTF-8 -*-

from .base import BaseSigner


class Signer(BaseSigner):
    site_name = "51acgwcy.com"
    url_login = "https://51acgwcy.com/wp-json/jwt-auth/v1/token"
    url_signin = "https://51acgwcy.com/wp-json/b2/v1/userMission"
    url_logout = "https://51acgwcy.com/wp-json/b2/v1/loginOut"

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
        self.s.headers["Authorization"] = "Bearer " + res.json().get("token")
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
