import logging
from pathlib import Path
from typing import Iterable, List, Union

from utils import media, xsession


class Bot:
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    def __init__(self) -> None:
        self.s = xsession.Bilibili()
        self.s.headers.update(self.headers)
        self.logger = logging.getLogger(__name__)

    def _get_safe_pixiv_illust_ids(self, num: int, history: List[str], blacklist: List[str], blacktags: List[str]) -> list:
        """Download proper pixiv illusts to dir "tmp/"

        Args

        num:
            how many illust ids should return
        history: 
            A list of dynamic illust history, to avoid upload same illusts
        blacklist: 
            A list of user ids, to avoid copyright problem
        blacktags:
            A list of banned tags

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
        def __safe_remove(l: List[str], r: Iterable[str]) -> None:
            """In place operation."""
            for e in r:
                try:
                    l.remove(e)
                except ValueError:
                    pass

        def _check_tags(tags: List[str]) -> bool:
            for t in blacktags:
                if t in tags:
                    return False
            return True

        s_pixiv = xsession.Pixiv()
        s_pixiv.headers.update(self.headers)

        # DEBUG
        # s_pixiv.proxies.update(self.proxies)

        # get proper illust info
        checked_illust_info = []  # ids has been checked  # {"id": "", "user_id": "", "username": "", "url": ""}
        success_illust_info = []  # successful ids # {"id": "", "user_id": "", "username": "", "url": "", "local_path": Path}
        cur_date = None
        while len(success_illust_info) < num:
            dynamic_illust_info = []  # current epoch illust info
            # get top 100
            rankings1 = s_pixiv.get_ranking(date=cur_date, content="illust", mode="monthly", p=1)
            rankings2 = s_pixiv.get_ranking(date=cur_date, content="illust", mode="monthly", p=2)
            if rankings1:
                rankings = rankings1
                rankings["contents"].extend(rankings2.get("contents", []))
            elif rankings2:
                rankings = rankings2
                rankings["contents"].extend(rankings1.get("contents", []))
            else:
                rankings = {}
            # if non-empty
            if rankings:
                cur_date = rankings["prev_date"]
                illust_ids = []
                for e in rankings["contents"]:
                    # set rules by ranking info
                    if int(e["illust_content_type"]["sexual"]) == 0 \
                            and int(e["illust_page_count"]) == 1 \
                            and str(e["illust_id"]) not in history \
                            and str(e["user_id"]) not in blacklist \
                            and _check_tags(e["tags"]):
                        illust_ids.append(str(e["illust_id"]))

                # choose proper illust
                # use safe_remove to avoid repeated illust id
                __safe_remove(illust_ids, [e["id"] for e in checked_illust_info])
                for illust_id in illust_ids:
                    illust_info = s_pixiv.get_illust(illust_id)
                    if illust_info:
                        if int(illust_info["sl"]) < 6:
                            dynamic_illust_info.append(
                                {
                                    "id": illust_id,
                                    "user_id": illust_info["userId"],
                                    "username": illust_info["userName"],
                                    "url": illust_info["urls"]["original"]
                                }
                            )

            # cache illust data
            for illust_info in dynamic_illust_info:
                url: str = illust_info["url"]
                path = Path("tmp", url.split("/")[-1])
                # download image if not exist
                if not path.is_file():
                    image_data = s_pixiv.get_page(url)
                    # limit picture size under 20 MB
                    if not image_data or len(image_data) > 19*1024*1024:
                        continue
                    path.write_bytes(image_data)
                illust_info["local_path"] = path
                success_illust_info.append(illust_info)

            # extend checked illust history
            checked_illust_info.extend(dynamic_illust_info)

        return success_illust_info[:num]

    def _get_random_bgm(self, playlist: str) -> dict:
        """
        Args

        playlist: 
            playlist id for kuwo music

        Returns

            Info of bgm
        """

    def login(self, usrn="", pwd="", cookies=None) -> bool:
        if cookies:
            self.s.cookies.update(cookies)
            return True
        self.logger.error("Bilibot:Failed to login.")
        return False
        # TODO: login
        raise NotImplementedError

    def logout(self) -> bool:
        if self.s.post_logout():
            return True
        self.logger.warning("Bilibot:Failed to logout.")
        return False

    def delete_dynamic(self, dynamic_id: str) -> bool:
        ret = self.s.post_rm_dynamic(dynamic_id)
        if not ret:
            self.logger.error("Bilibot:Failed to delete dynamic.")
            return False
        return True

    def is_dynamic_exist(self, dynamic_id: str) -> bool:
        """Check if a dynamic exist"""
        ret = self.s.get_dynamic_detail(dynamic_id)
        if ret and ret.get("result") == 0:
            return True
        return False

    def is_dynamic_auditing(self, dynamic_id: str) -> bool:
        """Check if a dynamic is being auditing

        Returns:
            bool: True if dynamic exist and being auditing, otherwise False
        """
        ret = self.s.get_dynamic_detail(dynamic_id)
        if ret and ret.get("result") == 0 and ret["card"].get("extra", {}).get("is_auditing") == 1:
            return True
        return False

    def create_pixiv_ranking_dynamic(self, history: List[str], blacklist: List[str], blacktags: List[str], count: int) -> dict:
        """
        Args

        history: 
            A list of dynamic illust history, to avoid upload same illusts
        blacklist: 
            A list of user ids, to avoid copyright problem
        blacktags:
            A list of banned illust tags
        count:
            the count for this dynamic

        Returns
        {
            "dynamic_id": "xxxx", 
            "illust_ids": ["xxx", "xxxx"]
        }
        """
        success_illust_info = self._get_safe_pixiv_illust_ids(9, history, blacklist, blacktags)
        local_illust_paths = [e["local_path"] for e in success_illust_info]

        # make text contents
        contents = "#动漫壁纸# #动漫美图# \n"
        contents += "（觉得不错的话，点个赞和关注吧，每天更新哦>؂<）\n"
        contents += "----------\n"
        contents += "【第{}期】ID画师按顺序：\n".format(count)
        for info in success_illust_info:
            contents += "{id}：{username}\n".format_map(info)

        dynamic_info = self.s.post_create_draw(contents, local_illust_paths)
        if not dynamic_info:
            self.logger.error("Bilibot:Failed to create draw.")
            return {}

        dynamic_id = dynamic_info["dynamic_id_str"]
        success_illust_ids = [info["id"] for info in success_illust_info]
        ret = {
            "dynamic_id": dynamic_id,
            "illust_ids": success_illust_ids
        }
        self.logger.info("Bilibot:create_pixiv_ranking_dynamic Success!")
        return ret

    def create_pixiv_ranking_video(self):
        raise NotImplementedError
