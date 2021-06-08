# -*- coding: UTF-8 -*-

import json
from argparse import ArgumentParser
from pathlib import Path
from base64 import b64decode

import utils

from . import cysll_com, jike0_com
from .base import BaseSigner

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("key_filepath")
    parser.add_argument("rsakey")

    args = parser.parse_args()
    with open(args.key_filepath, "r", encoding="utf8") as f:
        keys: dict = json.load(f)

    rsakey = args.rsakey
    rsakey = b64decode(rsakey).decode("utf8")

    sites = [cysll_com, jike0_com]
    for site in sites:
        Signer = site.Signer
        signer: BaseSigner = Signer(
            utils.rsa_decrypt(keys.get(Signer.site_name).get("usrn"), rsakey),
            utils.rsa_decrypt(keys.get(Signer.site_name).get("pwd"), rsakey)
        )
        signer.signin()
