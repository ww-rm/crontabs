# -*- coding: UTF-8 -*-

import json
import logging
import time
from argparse import ArgumentParser
from base64 import b64decode

import utils

from . import (acgwcy_com, cysll_com, jike0_com, www_bilibili_com,
               www_hmoe1_net, yingyun_pw)
from .base import BaseSigner

if __name__ == "__main__":
    # parse args
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("rsakey")
    parser.add_argument("--test", action="store_true", default=False)
    args = parser.parse_args()

    # logging config
    root_logger = logging.getLogger()
    fmter = logging.Formatter("{asctime} - {levelname} - {msg}", "%Y-%m-%d %H:%M:%S", "{")
    fmter.converter = time.gmtime
    if not args.test:
        root_logger.setLevel(logging.INFO)
        hdler = logging.FileHandler("logs/dailysignin.txt", encoding="utf8")
    else:
        root_logger.setLevel(logging.WARNING)
        hdler = logging.StreamHandler()
    hdler.setFormatter(fmter)
    root_logger.addHandler(hdler)

    # read config
    with open(args.config, "r", encoding="utf8") as f:
        config: dict = json.load(f)

    # read secrets
    rsakey = b64decode(args.rsakey).decode("utf8")
    def _d(p): return utils.secrets.rsa_decrypt(p, rsakey)

    # main works
    keys: dict = config.get("keys")
    sites = [
        cysll_com, jike0_com, acgwcy_com, yingyun_pw, www_hmoe1_net
    ]
    for site in sites:
        Signer = site.Signer
        signer: BaseSigner = Signer(
            _d(keys.get(Signer.site_name).get("usrn")),
            _d(keys.get(Signer.site_name).get("pwd"))
        )
        signer.signin()

    Signer = www_bilibili_com.Signer
    cookies = dict(map(
        lambda item: (item[0], _d(item[1])),
        keys.get(Signer.site_name).get("cookies").items()
    ))
    signer = Signer("", "", cookies=cookies)
    signer.signin()

    logging.shutdown()