# -*- coding: UTF-8 -*-

from datetime import datetime, timedelta, timezone


def getbeijingtime():
    """return Beijing time in format "%Y-%m-%d %H:%M:%S"
    """
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
