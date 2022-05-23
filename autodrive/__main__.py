import json
import logging
import time
from argparse import ArgumentParser
from pathlib import Path

import utils

from .pixivdrive import PixivDrive


def run(config):
    refresh_token = _d(config["refresh_token"])
    p_cookies = {k: _d(v) for k, v in config["pixiv"]["cookies"].items()}
    pixiv_drive = PixivDrive()
    if not pixiv_drive.login(refresh_token=refresh_token, p_cookies=p_cookies):
        logger.error("Failed to login, run failed.")
    else:
        # pixiv_drive.upload_illust("87954599", "./data/lena_gray.bmp")
        # exit(-1)
        pixiv_drive.upload_monthly_ranking(include_user_top=True)
        logger.info("Task completed.")

        # XXX: update refresh_token to config
        config["refresh_token"] = _e(pixiv_drive.s_adrive.refresh_token or refresh_token)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

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
        root_logger.setLevel(logging.WARNING)  # avoid big log file
        hdler = logging.FileHandler("logs/autodrive.txt", encoding="utf8")
    else:
        root_logger.setLevel(logging.WARNING)
        hdler = logging.StreamHandler()
    hdler.setFormatter(fmter)
    root_logger.addHandler(hdler)

    ####### DEBUG #######
    debug_hdl = logging.StreamHandler()
    debug_hdl.setFormatter(fmter)
    root_logger.addHandler(debug_hdl)
    #####################

    # read secrets
    def _e(p): return utils.secrets.aes256_enc_cbc(p, args.runkey)
    def _d(c): return utils.secrets.aes256_dec_cbc(c, args.runkey)

    # read config
    with Path(args.config).open("r", encoding="utf8") as f:
        config: dict = json.load(f)

    run(config)

    # save config
    with Path(args.config).open("w", encoding="utf8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    logging.shutdown()
