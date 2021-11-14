# -*- coding: UTF-8 -*-

import logging
from functools import wraps
from time import sleep

import requests


def empty_retry(times: int = 3, interval: float = 1):
    """Retry when a func returns empty

    Args:
        times (int): Times to retry.
        interval (float): Interval between each retry, in seconds.
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
    """A wrapper class for `requests.Session`, can log info.

    If anything wrong happened in a request, return an empty `Response` object, keeping url info and logging error info using `logging` module.
    """

    def __init__(self, interval: float = 0.01) -> None:
        """
        Args:
            interval (float): Seconds between each request. Minimum to 0.01.
        """
        super().__init__()
        self.interval = max(0.01, interval)
        self.logger = logging.getLogger(__name__)

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        sleep(self.interval)
        try:
            res = super().request(method, url, *args, **kwargs)
        except Exception as e:
            self.logger.error("{}:{}".format(url, e))
            res = requests.Response()
            res.url = url  # keep url info
        else:
            if not res.ok:
                self.logger.warning("{}:{}".format(url, res.status_code))
        finally:
            return res
