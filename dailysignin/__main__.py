# -*- coding: UTF-8 -*-

import json
from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path

import utils

from . import acgwcy_com, cysll_com, jike0_com, www_hmoe1_net, yingyun_pw
from .base import BaseSigner

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("key_filepath")
    parser.add_argument("rsakey")

    args = parser.parse_args()
    with open(args.key_filepath, "r", encoding="utf8") as f:
        keys: dict = json.load(f)

    rsakey = b64decode(args.rsakey).decode("utf8")
    _d = lambda p: utils.rsa_decrypt(p, rsakey)

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
