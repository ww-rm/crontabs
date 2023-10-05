# -*- coding: UTF-8 -*-

import json
import logging
import logging.handlers
import time
from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path

import utils
from dailysignin import owo_ecycloud_com

from . import (dash_pepsicola_me, freevpn_cyou, jike0_com, kkwcy_com, ssru6_pw,
               www_bilibili_com, www_hmoe11_net)


def run(config: dict):
    # main works
    keys: dict = config["keys"]

    kkwcy_com.Signer(_d(keys["kkwcy.com"]["usrn"]), _d(keys["kkwcy.com"]["pwd"])).signin()
    www_hmoe11_net.Signer(_d(keys["www.hmoe11.net"]["usrn"]), _d(keys["www.hmoe11.net"]["pwd"])).signin()

    jike0_com.Signer(_d(keys["jike0.com"]["usrn"]), _d(keys["jike0.com"]["pwd"])).signin()
    ssru6_pw.Signer(_d(keys["ssru6.pw"]["usrn"]), _d(keys["ssru6.pw"]["pwd"])).signin()
    freevpn_cyou.Signer(_d(keys["freevpn.cyou"]["usrn"]), _d(keys["freevpn.cyou"]["pwd"])).signin()
    dash_pepsicola_me.Signer(_d(keys["dash.pepsicola.me"]["usrn"]), _d(keys["dash.pepsicola.me"]["pwd"])).signin()
    # owo_ecycloud_com.Signer(_d(keys["owo.ecycloud.com"]["usrn"]), _d(keys["owo.ecycloud.com"]["pwd"])).signin()

    cookies = dict(map(lambda item: (item[0], _d(item[1])), keys["www.bilibili.com"]["cookies"].items()))
    # www_bilibili_com.Signer("", "", cookies=cookies).signin()


if __name__ == "__main__":
    # parse args
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("runkey")
    parser.add_argument("--test", action="store_true", default=False)
    args = parser.parse_args()

    # logging config
    root_logger = logging.getLogger()
    fmter = logging.Formatter("{asctime} - {levelname} - {filename} - {lineno} - {message}", "%Y-%m-%d %H:%M:%S", "{")
    fmter.converter = time.gmtime
    if not args.test:
        root_logger.setLevel(logging.INFO)
        hdler = logging.handlers.RotatingFileHandler("logs/dailysignin.txt", maxBytes=2**20, backupCount=2, encoding="utf8")
    else:
        root_logger.setLevel(logging.WARNING)
        hdler = logging.StreamHandler()
    hdler.setFormatter(fmter)
    root_logger.addHandler(hdler)

    # read config
    with Path(args.config).open("r", encoding="utf8") as f:
        config: dict = json.load(f)

    # read secrets
    def _d(c): return utils.secrets.aes256_dec_cbc(c, args.runkey)

    run(config)

    logging.shutdown()
