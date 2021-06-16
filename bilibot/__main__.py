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
    parser.add_argument("--test", action="store_ture", default=False)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf8") as f:
        config: dict = json.load(f)
    rsakey = b64decode(args.rsakey).decode("utf8")
    def _d(p): return utils.secrets.rsa_decrypt(p, rsakey)

    bot = Bot()
    cookies = dict(map(lambda item: (item[0], _d(item[1])), config.get("cookies").items()))
    if bot.login(cookies=cookies):
        # create_pixiv_ranking_dynamic
        history_path: str = config.get("pixiv").get("history")
        with Path(history_path).open("r", encoding="utf8") as f:
            history = json.load(f)
        blacklist = config.get("blacklist")

        ret = bot.create_pixiv_ranking_dynamic(history, blacklist)
        if ret:
            if args.test:
                bot.delete_dynamic(ret.get("dynamic_id"))
            else:
                # update history
                history.extend(ret.get("illust_ids"))
                with Path(history_path).open("w", encoding="utf8") as f:
                    json.dump(history, f, ensure_ascii=False)
