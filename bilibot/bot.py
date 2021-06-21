from datetime import datetime
from pathlib import Path
from typing import List, Union

from utils import xsession

from . import media


class Bot:
    log_path = "logs/bilibot.txt"
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    def __init__(self, log_path: Union[Path, str] = None) -> None:
        if log_path:
            self.log_path = log_path

        self.s = xsession.Bilibili(self.log_path)
        self.s.headers.update(self.headers)

    def _get_safe_pixiv_illust_ids(self, num: int, history: List[str], blacklist: List[str]) -> list:
        """Download proper pixiv illusts to dir "tmp/"

        Args

        num:
            how many illust ids should return
        history: 
            A list of dynamic illust history, to avoid upload same illusts
        blacklist: 
            A list of user ids, to avoid copyright problem

        Returns:
            A list of illust info, 
            {
                "id": str
                "user_id": str
                "username": str
                "url": str
                "local_path": Path
            }
        """

        s_pixiv = xsession.Pixiv(self.log_path)
        s_pixiv.headers.update(self.headers)
        # s_pixiv.proxies.update(self.proxies)
        history = history or []
        blacklist = blacklist or []

        # get proper illust info
        dynamic_illust_info = []
        # {
        #     "id": "",
        #     "user_id": "",
        #     "username": "",
        #     "url": ""
        # }
        cur_date = None
        while len(dynamic_illust_info) < num:
            rankings = s_pixiv.get_ranking(date=cur_date, content="illust", mode="monthly")
            if rankings:
                cur_date = rankings.get("prev_date")
                # choose no sexy illusts
                illust_ids = [
                    str(e.get("illust_id"))
                    for e in rankings.get("contents")
                    if e.get("illust_content_type").get("sexual") == 0  # set rules by ranking info
                ]

                # choose proper illust
                for illust_id in illust_ids:
                    if illust_id not in history:
                        illust_info = s_pixiv.get_illust(illust_id)
                        if illust_info:
                            # set rules by illust info
                            if (illust_info.get("userId") not in blacklist) and (illust_info.get("pageCount") == 1):
                                # not in history and user not in blacklist and pagecount == 1
                                dynamic_illust_info.append(
                                    {
                                        "id": illust_id,
                                        "user_id": illust_info.get("userId"),
                                        "username": illust_info.get("userName"),
                                        "url": illust_info.get("urls").get("original")
                                    }
                                )

        # cache illust data
        success_illust_info = []
        for illust_info in dynamic_illust_info[:num]:
            url: str = illust_info.get("url")
            path = Path("tmp", url.split("/")[-1])
            # download image if not exist
            if not path.is_file():
                image_data = s_pixiv.get_page(url)
                if image_data:
                    path.write_bytes(image_data)
                    illust_info["local_path"] = path
                    success_illust_info.append(illust_info)

        return success_illust_info

    def _get_random_bgm(self, playlist: str) -> dict:
        """
        Args

        playlist: 
            playlist id for kuwo music

        Returns

            Info of bgm
        """

    def log(self, msg, title="Bilibot"):
        current_time = datetime.utcnow().isoformat(timespec="seconds")
        log_msg = "{}\t{} : {}".format(current_time, title, msg)

        with Path(self.log_path).open("a", encoding="utf8") as f:
            print(log_msg, file=f)

    def login(self, usrn="", pwd="", cookies=None) -> bool:
        if cookies:
            self.s.cookies.update(cookies)
            return True
        self.log("Failed to login.")
        return False
        # TODO: login
        raise NotImplementedError

    def logout(self) -> bool:
        if self.s.post_logout():
            return True
        self.log("Failed to logout.")
        return False

    def delete_dynamic(self, dynamic_id: str) -> bool:
        ret = self.s.post_rm_dynamic(dynamic_id)
        if not ret:
            self.log("Failed to delete dynamic.")
            return False
        return True

    def create_pixiv_ranking_dynamic(self, history: List[str] = None, blacklist: List[str] = None) -> dict:
        """
        Args

        history: 
            A list of dynamic illust history, to avoid upload same illusts
        blacklist: 
            A list of user ids, to avoid copyright problem

        Returns
        {
            "dynamic_id": "xxxx", 
            "illust_ids": ["xxx", "xxxx"]
        }
        """
        success_illust_info = self._get_safe_pixiv_illust_ids(9, history, blacklist)
        local_illust_paths = [e.get("local_path") for e in success_illust_info]

        # make text contents
        contents = "\u0023\u52a8\u6f2b\u58c1\u7eb8\u0023 \u0023\u52a8\u6f2b\u7f8e\u56fe\u0023 \n"
        contents += "\u0049\u0044\u753b\u5e08\u6309\u987a\u5e8f\uff1a\n"
        for info in success_illust_info:
            contents += "{id} \uff1a{username}\n".format_map(info)
        contents += "\uff08\u8f6c\u8f7d\u81ea\u0050\u0069\u0078\u0069\u0076\uff0c\u4fb5\u5220\uff09\n"

        dynamic_info = self.s.post_create_draw(contents, local_illust_paths)
        if not dynamic_info:
            self.log("Failed to create draw.")
            return {}

        dynamic_id = dynamic_info.get("dynamic_id_str")
        success_illust_ids = [info.get("id") for info in success_illust_info]
        ret = {
            "dynamic_id": dynamic_id,
            "illust_ids": success_illust_ids
        }
        self.log("create_pixiv_ranking_dynamic Success!")
        return ret

    def create_pixiv_ranking_video(self):
        raise NotImplementedError
