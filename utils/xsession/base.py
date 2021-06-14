# -*- coding: UTF-8 -*-

import io
import sys
from pathlib import Path
from time import sleep

import requests
from utils import helper


class XSession(requests.Session):
    """A wrapper class for requests.Session, can control log path

    If anything wrong happened in a request, return an empty Response object and log error info to logfile
    """

    def __init__(self, logfile=None, interval: float = 0.1) -> None:
        """
        Args:
            logfile: A file-like or path-like object. Default to sys.stderr
            interval: Seconds between each request. Default to 0.1
        """
        super().__init__()
        self.logfile = logfile or sys.stderr
        self.interval = interval or 0.1

    def request(self, method, url, *args, **kwargs):
        try:
            sleep(self.interval)
            return super().request(method, url, *args, **kwargs)
        except Exception as e:
            if isinstance(self.logfile, io.IOBase):
                print("{} : {}".format(helper.getbeijingtime(), str(e)), file=self.logfile)
            else:
                with Path(self.logfile).open("a", encoding="utf8") as f:
                    print("{} : {}".format(helper.getbeijingtime(), str(e)), file=f)
            return requests.Response()
