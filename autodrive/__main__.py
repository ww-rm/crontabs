import json
import logging
import time
from argparse import ArgumentParser
from base64 import b64decode

import utils

from .pixivdrive import PixivDrive


def run(config):
    refresh_token = _d(config["refresh_token"])
    p_cookies = {k: _d(v) for k, v in config["pixiv"]["cookies"].items()}
    pixiv_drive = PixivDrive()
    if not pixiv_drive.login(refresh_token=refresh_token, p_cookies=p_cookies):
        logger.error("Failed to login, run failed.")
    else:
        pixiv_drive.upload_monthly_ranking(include_user_top=True)
        logger.info("Task completed.")


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # parse args
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("rsakey")
    parser.add_argument("--test", action="store_true", default=False)
    args = parser.parse_args()

    # read config
    with open(args.config, "r", encoding="utf8") as f:
        config: dict = json.load(f)

    # read secrets
    rsakey = b64decode(args.rsakey).decode("utf8")
    def _d(p): return utils.secrets.rsa_decrypt(p, rsakey)

    # logging config
    root_logger = logging.getLogger()
    fmter = logging.Formatter("{asctime} - {levelname} - {filename} - {lineno} - {message}", "%Y-%m-%d %H:%M:%S", "{")
    fmter.converter = time.gmtime
    if not args.test:
        root_logger.setLevel(logging.ERROR) # avoid big log file
        hdler = logging.FileHandler("logs/autodrive.txt", encoding="utf8")
    else:
        root_logger.setLevel(logging.WARNING)
        hdler = logging.StreamHandler()
    hdler.setFormatter(fmter)
    root_logger.addHandler(hdler)

    run(config)

    logging.shutdown()
