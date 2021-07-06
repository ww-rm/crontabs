# -*- coding: UTF-8 -*-

import json
import logging
import time
from argparse import ArgumentParser
from base64 import b64decode

import utils

from . import (acgwcy_com, cysll_com, jike0_com, socloud_me, www_bilibili_com,
               www_hmoe1_net, yingyun_pw)


def run(config: dict):
    # main works
    keys: dict = config["keys"]

    cysll_com.Signer(_d(keys["cysll.com"]["usrn"]), _d(keys["cysll.com"]["pwd"])).signin()
    jike0_com.Signer(_d(keys["jike0.com"]["usrn"]), _d(keys["jike0.com"]["pwd"])).signin()
    acgwcy_com.Signer(_d(keys["51acgwcy.com"]["usrn"]), _d(keys["51acgwcy.com"]["pwd"])).signin()
    yingyun_pw.Signer(_d(keys["yingyun-f.pw"]["usrn"]), _d(keys["yingyun-f.pw"]["pwd"])).signin()
    www_hmoe1_net.Signer(_d(keys["www.hmoe1.net"]["usrn"]), _d(keys["www.hmoe1.net"]["pwd"])).signin()
    socloud_me.Signer(_d(keys["socloud.me"]["usrn"]), _d(keys["socloud.me"]["pwd"])).signin()

    cookies = dict(map(lambda item: (item[0], _d(item[1])), keys["www.bilibili.com"]["cookies"].items()))
    www_bilibili_com.Signer("", "", cookies=cookies).signin()


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

    run(config)

    logging.shutdown()
