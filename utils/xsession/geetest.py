# -*- coding: UTF-8 -*-

import json
import bs4
from .base import XSession


class Geetest(XSession):
    def __init__(self, interval: float = 0.01) -> None:
        super().__init__(interval=interval)