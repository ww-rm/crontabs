# -*- coding: UTF-8 -*-

import logging
from functools import wraps
from time import sleep

import requests


def empty_retry(times=3, interval=1):
    """Retry when a func returns empty

    Args

    times:
        how many times to retry
    interval:
        interval between each retry, in seconds
    """
    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            for _ in range(times):
                ret = func(*args, **kwargs)
                if ret:
                    return ret
                sleep(interval)
            logging.getLogger(__name__).error("All retries failed in func {}.".format(func.__name__))
            return ret
        return decorated_func
    return decorator


class XSession(requests.Session):
    """A wrapper class for requests.Session, can control log path

    If anything wrong happened in a request, return an empty Response object and log error info using `logging` module
    """

    def __init__(self, interval: float = 0.01) -> None:
        """
        Args:
            interval: Seconds between each request. Default to 0.1
        """
        super().__init__()
        self.interval = interval or 0.01
        self.logger = logging.getLogger(__name__)

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        try:
            sleep(self.interval)
            return super().request(method, url, *args, **kwargs)
        except Exception as e:
            self.logger.error("{}:{}".format(url, e))
            return requests.Response()
