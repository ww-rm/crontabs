# -*- coding: UTF-8 -*-

import logging
from functools import wraps
from time import sleep
from typing import Tuple, Union

import requests
from requests.adapters import HTTPAdapter


def empty_retry(times: int = 3, interval: float = 1):
    """Retry when a func returns empty

    Args:
        times (int): Times to retry.
        interval (float): Interval between each retry, in seconds.
    """
    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kwargs):
            for i in range(times + 1):
                # retry log
                if i > 0:
                    logging.getLogger(__name__).warning("Retry func {} {} time.".format(func.__name__, i))

                # call func
                ret = func(*args, **kwargs)
                if ret:
                    return ret

                # sleep for interval
                sleep(interval)

            # all retry failed
            logging.getLogger(__name__).error("All retries failed in func {}.".format(func.__name__))
            return ret
        return decorated_func
    return decorator


class XSession(requests.Session):
    """A wrapper class for `requests.Session`, can log info.

    If anything wrong happened in a request, return an empty `Response` object, keeping url info and logging error info using `logging` module.
    """

    def __init__(self) -> None:
        """
        Properties:
            interval (float): Seconds between each request. Minimum to 0.01. Default to 0.01
            max_retries (int): max retry times. Default to 3.
            timeout: same as timeout param to `requests.request`, default to 30.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.interval = 0.01
        self.timeout = 30
        self.max_retries = 3

    @property
    def interval(self):
        return self.__interval

    @interval.setter
    def interval(self, value: float):
        self.__interval = max(0.01, value)

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, value: Union[Tuple[float, float], float]):
        self.__timeout = value

    @property
    def max_retries(self):
        return self.__max_retries

    @max_retries.setter
    def max_retries(self, value: int):
        self.__max_retries = value
        # set default adapter max retry
        self.mount("https://", HTTPAdapter(max_retries=value))
        self.mount("http://", HTTPAdapter(max_retries=value))

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        sleep(self.interval)
        kwargs.setdefault("timeout", self.timeout)  # timeout to avoid suspended
        try:
            res = super().request(method, url, *args, **kwargs)
        except Exception as e:
            self.logger.error("{}:{}".format(url, e))
            res = requests.Response()
            res.url = url  # keep url info
            return res
        else:
            if not res.ok:
                self.logger.warning("{}:{}".format(url, res.status_code))
            return res
