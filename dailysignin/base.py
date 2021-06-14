# -*- coding: UTF-8 -*-

from datetime import datetime
from pathlib import Path

from utils import xsession


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

        self.s = xsession.XSession(self.log_path)
        self.s.headers.update(self.headers)
        if useproxies:
            self.s.proxies.update(self.proxies)

    def log(self, msg: str):
        """Log with site name and message"""
        current_time = datetime.utcnow().isoformat(timespec="seconds")
        log_msg = "{}\t{} : {}".format(current_time, self.site_name, msg)
        
        with Path(self.log_path).open("a", encoding="utf8") as f:
            print(log_msg, file=f)

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
        res_val = True
        if not self._login():
            self.log("Failed to login.")
            res_val = False
        else:
            if not self._signin():
                self.log("Failed to sign in.")
                res_val = False
            if not self._logout():
                self.log("Failed to logout.")
                res_val = False

        if res_val:
            self.log("All Success!")
        return res_val
