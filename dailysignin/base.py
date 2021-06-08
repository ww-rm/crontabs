# -*- coding: UTF-8 -*-

from pathlib import Path

import utils


class BaseSigner:
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }
    log_path = "logs/dailysignin.txt"
    site_name = "signer.base"

    def __init__(self, usrn: str, pwd: str, useproxies=False, log_path=None) -> None:
        self.usrn = usrn
        self.pwd = pwd
        if log_path:
            self.log_path = log_path

        self.s = utils.XSession(self.log_path)
        self.s.headers = self.headers
        if useproxies:
            self.s.proxies = self.proxies

    def log(self, msg: str):
        """Log with site name and message"""
        with Path(self.log_path).open("a", encoding="utf8") as f:
            print("{} : {} : {}".format(utils.getbeijingtime(), self.site_name, msg), file=f)

    def _login(self) -> bool:
        """Login"""
        raise NotImplementedError

    def _signin(self) -> bool:
        """Sign in"""
        raise NotImplementedError

    def _logout(self) -> bool:
        """Logout"""
        raise NotImplementedError

    def signin(self) -> bool:
        if not self._login():
            self.log("Failed to login.")
            return False
        if not self._signin():
            self.log("Failed to sign in.")
            return False
        if not self._logout():
            self.log("Failed to logout.")
            return True

        self.log("Success!")
        return True
