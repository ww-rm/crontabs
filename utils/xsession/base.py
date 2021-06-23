# -*- coding: UTF-8 -*-

import logging
from time import sleep

import requests


class XSession(requests.Session):
    """A wrapper class for requests.Session, can control log path

    If anything wrong happened in a request, return an empty Response object and log error info using `logging` module
    """

    def __init__(self, interval: float = 0.1) -> None:
        """
        Args:
            interval: Seconds between each request. Default to 0.1
        """
        super().__init__()
        self.interval = interval or 0.1
        self.logger = logging.getLogger(__name__)

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        try:
            sleep(self.interval)
            return super().request(method, url, *args, **kwargs)
        except Exception as e:
            self.logger.error("{}:{}".format(url, e))
            return requests.Response()
