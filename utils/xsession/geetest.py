# -*- coding: UTF-8 -*-

import json
import bs4
from .base import XSession


class Geetest(XSession):
    def __init__(self, logfile=None, interval: float = 0.1) -> None:
        super().__init__(logfile=logfile, interval=interval)