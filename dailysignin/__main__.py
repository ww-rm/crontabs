# -*- coding: UTF-8 -*-

import json
import logging
import time
from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path

import utils

from . import (freevpn_cyou, jike0_com, kkwcy_com, socloud_me, www_q88q_cyou,
               ssru6_pw, www_bilibili_com, www_hmoe11_net)


def run(config: dict):
    # main works
    keys: dict = config["keys"]

    kkwcy_com.Signer(_d(keys["kkwcy.com"]["usrn"]), _d(keys["kkwcy.com"]["pwd"])).signin()
    www_hmoe11_net.Signer(_d(keys["www.hmoe11.net"]["usrn"]), _d(keys["www.hmoe11.net"]["pwd"])).signin()

    jike0_com.Signer(_d(keys["jike0.com"]["usrn"]), _d(keys["jike0.com"]["pwd"])).signin()
    # socloud_me.Signer(_d(keys["socloud.me"]["usrn"]), _d(keys["socloud.me"]["pwd"])).signin()
    ssru6_pw.Signer(_d(keys["ssru6.pw"]["usrn"]), _d(keys["ssru6.pw"]["pwd"])).signin()
    # www_q88q_cyou.Signer(_d(keys["www.q88q.cyou"]["usrn"]), _d(keys["www.q88q.cyou"]["pwd"])).signin()
    freevpn_cyou.Signer(_d(keys["freevpn.cyou"]["usrn"]), _d(keys["freevpn.cyou"]["pwd"])).signin()

    cookies = dict(map(lambda item: (item[0], _d(item[1])), keys["www.bilibili.com"]["cookies"].items()))
    www_bilibili_com.Signer("", "", cookies=cookies).signin()


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
        hdler = logging.FileHandler("logs/dailysignin.txt", encoding="utf8")
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
