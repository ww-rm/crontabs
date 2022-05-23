import json
import logging
import time
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path

import utils

from .bot import Bot


def run(config: dict):
    # load bilibot data
    data_path: str = config["data_file"]
    with Path(data_path).open("r", encoding="utf8") as f:
        bilibot_data: dict = json.load(f)

    # main works
    bot = Bot()
    cookies = {k: _d(v) for k, v in config["cookies"].items()}
    if bot.login(cookies=cookies):
        today = datetime.utcnow()

        # dynamic task
        latest_dynamic_id = bilibot_data["latest_dynamic_id"]
        # exist and not being auditing
        if bot.is_dynamic_exist(latest_dynamic_id):
            if bot.is_dynamic_auditing(latest_dynamic_id):
                logger.info("Last dynamic being auditing.")
            else:
                last_update_date = datetime.fromisoformat(bilibot_data["last_update_date"])
                time_delta = (today - last_update_date).total_seconds()
                # if at least 5 hours before last update
                if time_delta > 3600*5:
                    logger.info("{:.0f} seconds before last successful new update, try create new one.".format(time_delta))

                    # do create_pixiv_ranking_dynamic
                    ret = bot.create_pixiv_ranking_dynamic(
                        history=bilibot_data["illust_history"],
                        blacklist=config["pixiv"]["blacklist"],
                        blacktags=config["pixiv"]["blacktags"],
                        count=bilibot_data["dynamic_count"] + 1
                    )
                    if ret:
                        # update date only when success create dynamic
                        bilibot_data["last_update_date"] = (today - timedelta(minutes=10)).isoformat(" ", "seconds")

                        # update count
                        bilibot_data["dynamic_count"] += 1

                        # update data
                        bilibot_data["latest_dynamic_id"] = ret["dynamic_id"]
                        bilibot_data["illust_history"].extend(ret["illust_ids"])
                        # limit size, the latest 10000 illust ids
                        bilibot_data["illust_history"] = bilibot_data["illust_history"][-10000:]
        else:
            logger.info("Last dynamic don't exist, redo create dynamic task.")
            # redo create_pixiv_ranking_dynamic
            ret = bot.create_pixiv_ranking_dynamic(
                history=bilibot_data["illust_history"],
                blacklist=config["pixiv"]["blacklist"],
                blacktags=config["pixiv"]["blacktags"],
                count=bilibot_data["dynamic_count"]
            )
            if ret:
                # update date only when success create dynamic
                bilibot_data["last_update_date"] = (today - timedelta(minutes=10)).isoformat(" ", "seconds")

                # update data
                bilibot_data["latest_dynamic_id"] = ret["dynamic_id"]
                bilibot_data["illust_history"].extend(ret["illust_ids"])
                # limit size, the latest 10000 illust ids
                bilibot_data["illust_history"] = bilibot_data["illust_history"][-10000:]

        # TODO: create video

    # save bilibot data
    with Path(data_path).open("w", encoding="utf8") as f:
        json.dump(bilibot_data, f, ensure_ascii=False, indent=4)


def test(config: dict):
    # load bilibot data
    data_path: str = config["data_file"]
    with Path(data_path).open("r", encoding="utf8") as f:
        bilibot_data: dict = json.load(f)

    # main works
    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config["cookies"].items()))
    if bot.login(cookies=cookies):
        # test create_pixiv_ranking_dynamic
        ret = bot.create_pixiv_ranking_dynamic(
            history=bilibot_data["illust_history"],
            blacklist=config["pixiv"]["blacklist"],
            blacktags=config["pixiv"]["blacktags"],
            count=bilibot_data["dynamic_count"] + 1
        )
        if ret:
            bot.delete_dynamic(ret["dynamic_id"])

        # TODO: test video ?


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # parse args
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("runkey")
    parser.add_argument("--test", action="store_true", default=False)
    args = parser.parse_args()

    # read config
    with Path(args.config).open("r", encoding="utf8") as f:
        config: dict = json.load(f)

    # read secrets
    def _d(c): return utils.secrets.aes256_dec_cbc(c, args.runkey)

    # logging config
    root_logger = logging.getLogger()
    fmter = logging.Formatter("{asctime} - {levelname} - {filename} - {lineno} - {message}", "%Y-%m-%d %H:%M:%S", "{")
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
