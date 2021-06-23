import json
from argparse import ArgumentParser
from base64 import b64decode
import logging
from pathlib import Path
import time

import utils

from .bot import Bot

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
        hdler = logging.FileHandler("logs/bilibot.txt", encoding="utf8")
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
    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config.get("cookies").items()))
    if bot.login(cookies=cookies):
        # load history data
        pixiv_data_path: str = config.get("pixiv").get("data_file")
        with Path(pixiv_data_path).open("r", encoding="utf8") as f:
            bilibot_data: dict = json.load(f)

        # create_pixiv_ranking_dynamic
        ret = bot.create_pixiv_ranking_dynamic(
            bilibot_data.get("history"), 
            config.get("pixiv").get("blacklist"),
            config.get("pixiv").get("blacktags")
        )
        if ret:
            if args.test:
                bot.delete_dynamic(ret.get("dynamic_id"))
            else:
                # update data
                bilibot_data["count"] = bilibot_data.get("count", 0) + 1
                bilibot_data.get("history").extend(ret.get("illust_ids"))
                # limit size, the latest 100000 illust ids
                bilibot_data["history"] = bilibot_data.get("history")[-100000:]
                with Path(pixiv_data_path).open("w", encoding="utf8") as f:
                    json.dump(bilibot_data, f, ensure_ascii=False, indent=4)

    logging.shutdown()