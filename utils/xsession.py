# -*- coding: UTF-8 -*-

from pathlib import Path
from time import sleep

import requests

from .helper import getbeijingtime


class XSession(requests.Session):
    """A wrapper class for requests.Session, can control log path

    If anything wrong happened in a request, return an empty Response object and log error info to log_path
    """

    def __init__(self, log_path) -> None:
        super().__init__()
        self.log_path = log_path

    def request(self, method, url, *args, **kwargs):
        try:
            sleep(0.1)
            return super().request(method, url, *args, **kwargs)
        except Exception as e:
            with Path(self.log_path).open("a", encoding="utf8") as f:
                print("{} : {}".format(getbeijingtime(), str(e)), file=f)
            return requests.Response()
