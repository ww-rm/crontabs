# -*- coding: UTF-8 -*-

import json
import bs4
from .base import XSession


class Bilibili(XSession):
    # lang=zh
    url_host = "https://www.bilibili.com/"

    def __init__(self, logfile=None, interval: float = 0.1, cookies: dict = None) -> None:
        super().__init__(logfile=logfile, interval=interval)
        if cookies:
            for name, value in cookies.items():
                self.cookies.set(name, value, domain="bilibili.com", path="/")
        # print(cookies)
