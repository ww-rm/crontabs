# -*- coding: UTF-8 -*-

import io
import sys
from datetime import datetime
from pathlib import Path
from time import sleep

import requests


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

    def log(self, url: str, msg: str):
        current_time = datetime.utcnow().isoformat(timespec="seconds")
        log_msg = "{}\t{} : {}".format(current_time, url, msg)

        if isinstance(self.logfile, io.IOBase):
            print(log_msg, file=self.logfile)
        else:
            with Path(self.logfile).open("a", encoding="utf8") as f:
                print(log_msg, file=f)

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        try:
            sleep(self.interval)
            return super().request(method, url, *args, **kwargs)
        except Exception as e:
            self.log(url, str(e))
            return requests.Response()
