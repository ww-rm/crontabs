import json
from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path

import utils

from .bot import Bot

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("rsakey")
    parser.add_argument("--test", action="store_true", default=False)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf8") as f:
        config: dict = json.load(f)
    rsakey = b64decode(args.rsakey).decode("utf8")
    def _d(p): return utils.secrets.rsa_decrypt(p, rsakey)

    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config.get("cookies").items()))
    if bot.login(cookies=cookies):
        # load history data
        data_path: str = config.get("pixiv").get("data_file")
        with Path(data_path).open("r", encoding="utf8") as f:
            bilibot_data: dict = json.load(f)

        # create_pixiv_ranking_dynamic
        ret = bot.create_pixiv_ranking_dynamic(
            bilibot_data.get("history"), 
            config.get("blacklist")
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
                with Path(data_path).open("w", encoding="utf8") as f:
                    json.dump(bilibot_data, f, ensure_ascii=False)
