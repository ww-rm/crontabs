import json
import logging
import time
from argparse import ArgumentParser
from base64 import b64decode
from datetime import datetime
from pathlib import Path

import utils

from .bot import Bot


def run(config):
    # load bilibot data
    data_path: str = config.get("data_file")
    with Path(data_path).open("r", encoding="utf8") as f:
        bilibot_data: dict = json.load(f)

    # main works
    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config.get("cookies").items()))
    if bot.login(cookies=cookies):
        today = datetime.utcnow()
        last_update_date = datetime.fromisoformat(bilibot_data.get("last_update_date"))

        # if at least 1 day before last update
        if (today - last_update_date).days > 0:
            # update date
            bilibot_data["last_update_date"] = today.isoformat(" ", "seconds")

            # create_pixiv_ranking_dynamic
            ret = bot.create_pixiv_ranking_dynamic(
                bilibot_data.get("illust_history"),
                config.get("pixiv").get("blacklist"),
                config.get("pixiv").get("blacktags")
            )
            if ret:
                # update data
                bilibot_data["dynamic_count"] = bilibot_data.get("count", 0) + 1
                bilibot_data["latest_dynamic_id"] = ret.get("dynamic_id")
                bilibot_data.get("history").extend(ret.get("illust_ids"))
                # limit size, the latest 100000 illust ids
                bilibot_data["illust_history"] = bilibot_data.get("illust_history")[-100000:]

            # TODO: create video

        else:
            # check dynamic
            latest_dynamic_id = bilibot_data.get("latest_dynamic_id")
            # TODO: not exist
            if False:
                # redo create_pixiv_ranking_dynamic
                ret = bot.create_pixiv_ranking_dynamic(
                    bilibot_data.get("illust_history"),
                    config.get("pixiv").get("blacklist"),
                    config.get("pixiv").get("blacktags")
                )
                if ret:
                    # update data
                    bilibot_data["latest_dynamic_id"] = ret.get("dynamic_id")
                    bilibot_data.get("history").extend(ret.get("illust_ids"))
                    # limit size, the latest 100000 illust ids
                    bilibot_data["illust_history"] = bilibot_data.get("illust_history")[-100000:]

    # save bilibot data
    with Path(data_path).open("w", encoding="utf8") as f:
        json.dump(bilibot_data, f, ensure_ascii=False, indent=4)


def test(config):
    # load bilibot data
    data_path: str = config.get("data_file")
    with Path(data_path).open("r", encoding="utf8") as f:
        bilibot_data: dict = json.load(f)

    # main works
    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config.get("cookies").items()))
    if bot.login(cookies=cookies):
        # test create_pixiv_ranking_dynamic
        ret = bot.create_pixiv_ranking_dynamic(
            bilibot_data.get("illust_history"),
            config.get("pixiv").get("blacklist"),
            config.get("pixiv").get("blacktags")
        )
        if ret:
            bot.delete_dynamic(ret.get("dynamic_id"))

        # TODO: test video ?


if __name__ == "__main__":
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
    fmter = logging.Formatter("{asctime} - {levelname} - {msg}", "%Y-%m-%d %H:%M:%S", "{")
    fmter.converter = time.gmtime

    if not args.test:
        # logging config
        root_logger.setLevel(logging.INFO)
        hdler = logging.FileHandler("logs/bilibot.txt", encoding="utf8")
        hdler.setFormatter(fmter)
        root_logger.addHandler(hdler)
        run(config)
    else:
        # logging config
        root_logger.setLevel(logging.WARNING)
        hdler = logging.StreamHandler()
        hdler.setFormatter(fmter)
        root_logger.addHandler(hdler)
        test(config)

    logging.shutdown()
