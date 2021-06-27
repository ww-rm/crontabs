# -*- coding: UTF-8 -*-

import logging

from utils import xsession


class BaseSigner:
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }
    site_name = "signer.base"

    def __init__(self, usrn: str, pwd: str, useproxies=False) -> None:
        self.usrn = usrn
        self.pwd = pwd
        self.logger = logging.getLogger(__name__)

        self.s = xsession.XSession()
        self.s.headers.update(self.headers)
        if useproxies:
            self.s.proxies.update(self.proxies)

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
            self.logger.error("{}:{}".format(self.site_name, "Failed to login."))
            res_val = False
        else:
            if not self._signin():
                self.logger.warning("{}:{}".format(self.site_name, "Failed to sign in."))
                res_val = False
            if not self._logout():
                self.logger.warning("{}:{}".format(self.site_name, "Failed to logout."))
                res_val = False

        if res_val:
            self.logger.info("{}:{}".format(self.site_name, "All Success!"))
        return res_val
