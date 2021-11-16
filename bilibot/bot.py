import logging
import random
from pathlib import Path
from typing import Iterable, List, Union
from utils.xsession.base import empty_retry

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
        self.s_bili = xsession.Bilibili()
        self.s_bili.headers.update(self.headers)
        self.logger = logging.getLogger(__name__)

    def _get_safe_pixiv_illust_ids(
        self, num: int,
        history: List[int], blacklist: List[int], blacktags: List[str], choosetags: List[str], *,
        sl: int = 5
    ) -> List[dict]:
        """Download proper pixiv illusts to dir "tmp/"

        Args:
            num: how many illust ids should return.
            history: A list of dynamic illust history, to avoid upload same illusts.
            blacklist: A list of user ids, to avoid copyright problem.
            blacktags: A list of banned tags.
            choosetags: A list of chosen tags.

            sl (int): Sex level ? the higher, the sexier

        Returns:
            A list of illust info, 
            {
                "id": int
                "user_id": int
                "username": str
                "url": str
                "local_path": Path
            }
        """
        def __safe_remove(l: List[int], r: Iterable[int]) -> None:
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

        def _choose_tags(tags: List[str]) -> bool:
            for t in choosetags:
                if t not in tags:
                    return False
            return True

        s_pixiv = xsession.Pixiv()
        s_pixiv.headers.update(self.headers)

        # DEBUG
        # s_pixiv.proxies.update(self.proxies)

        history = set(history)  # reduce look up time

        # get proper illust info
        success_illust_info = []  # successful ids # {"id": 123, "user_id": 123, "username": "", "url": "", "local_path": Path}
        cur_date = None
        while len(success_illust_info) < num:
            dynamic_illust_info = []  # current epoch illust info
            # get top 100 monthly illust
            rankings1 = s_pixiv.get_ranking_monthly(p=1, date=cur_date)
            rankings2 = s_pixiv.get_ranking_monthly(p=2, date=cur_date)
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
                            and int(e["illust_id"]) not in history \
                            and int(e["user_id"]) not in blacklist \
                            and _check_tags(e["tags"]) \
                            and _choose_tags(e["tags"]):
                        illust_ids.append(int(e["illust_id"]))

                # shuffle illust_ids
                for _ in range(50):
                    random.shuffle(illust_ids)

                # choose proper illust
                # use safe_remove to avoid repeated illust id
                __safe_remove(illust_ids, [e["id"] for e in success_illust_info])
                for illust_id in illust_ids:
                    illust_info = s_pixiv.get_illust(illust_id)
                    if illust_info:
                        if int(illust_info["sl"]) <= sl:
                            dynamic_illust_info.append(
                                {
                                    "id": int(illust_id),
                                    "user_id": int(illust_info["userId"]),
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
                    # get image data
                    if not s_pixiv.download_page(url, path):
                        continue
                    # limit picture size under 20 MB
                    if path.stat().st_size > 19*1024*1024:
                        continue
                illust_info["local_path"] = path
                success_illust_info.append(illust_info)

        return success_illust_info[:num]

    @empty_retry()
    def _get_random_bgm(self, playlist: List[int]) -> dict:
        """
        Args

        playlist: 
            playlist id for kuwo music

        Returns
            dict: song save path and infos, `name`, `artist`, `local_path`
        """
        s_kuwo = xsession.KuwoMusic()
        s_kuwo.headers.update(self.headers)
        id_ = random.choice(playlist)

        # BUG
        raise NotImplementedError

        song_info = s_kuwo.get_music_info(id_)
        song_data = s_kuwo.get_song_data(id_)
        if not song_info or not song_data:
            return {}

        # cache file to local
        cache_path = Path("tmp/bgm.mp3")
        cache_path.write_bytes(song_data)
        result = {
            "name": song_info.get("name"),
            "artist": song_info.get("artist"),
            "local_path": cache_path
        }

        return result

    def login(self, usrn: str = "", pwd: str = "", *, cookies: dict = None) -> bool:
        return self.s_bili.login(usrn, pwd, cookies=cookies)

    def logout(self) -> bool:
        return self.s_bili.logout()

    def is_dynamic_exist(self, dynamic_id: int) -> bool:
        """Check if a dynamic exist"""
        ret = self.s_bili.get_dynamic_detail(dynamic_id)
        if ret and ret.get("result") == 0:
            return True
        return False

    def is_dynamic_auditing(self, dynamic_id: int) -> bool:
        """Check if a dynamic is being auditing

        Returns:
            bool: True if dynamic exist and being auditing, otherwise False
        """
        ret = self.s_bili.get_dynamic_detail(dynamic_id)
        if ret and ret.get("result") == 0 and ret["card"].get("extra", {}).get("is_auditing") == 1:
            return True
        return False

    def create_pixiv_ranking_dynamic(self, history: List[int], blacklist: List[int], blacktags: List[str], count: int) -> dict:
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
            "dynamic_id": 123, 
            "illust_ids": [123, 456]
        }
        """
        success_illust_info = self._get_safe_pixiv_illust_ids(9, history, blacklist, blacktags, [])
        local_illust_paths = [e["local_path"] for e in success_illust_info]

        # make text contents
        contents = "#动漫壁纸# #动漫美图# \n"
        contents += "【第{}期】（觉得不错的话，点个赞和关注吧，每天更新哦>؂<）\n".format(count)
        contents += "--------------------------------------------------\n"
        contents += "ID画师按顺序：\n"
        for info in success_illust_info:
            contents += "{id}：{username}\n".format_map(info)

        dynamic_info = self.s_bili.create_dynamic(contents, local_illust_paths)
        if not dynamic_info:
            self.logger.error("Failed to create ranking dynamic.")
            return {}

        dynamic_id = dynamic_info["dynamic_id"]
        success_illust_ids = [info["id"] for info in success_illust_info]
        ret = {
            "dynamic_id": dynamic_id,
            "illust_ids": success_illust_ids
        }
        self.logger.info("Create ranking dynamic Success!")
        return ret

    def create_pixiv_ranking_video(self, history: List[int], blacklist: List[int], blacktags: List[str], bgmlist: List[int], count: int) -> dict:
        """
        Args

        history: 
            A list of dynamic illust history, to avoid upload same illusts
        blacklist: 
            A list of user ids, to avoid copyright problem
        blacktags:
            A list of banned illust tags
        count:
            the count for this video
        """
        # get illusts
        success_illust_info = self._get_safe_pixiv_illust_ids(30, history, blacklist, blacktags, ["女の子"], mode="weekly")
        local_illust_paths = [e["local_path"] for e in success_illust_info]

        # get bgm
        bgm_info = self._get_random_bgm(bgmlist)
        bgm_path = bgm_info.get("local_path")

        # make video to local
        video_path = media.make_video(media.load_images(local_illust_paths), "tmp/video.mp4", bgm_path)

        ##########################
        # TODO: LOCAL TEST
        ##########################
        # choose cover image
        # upload video
        # make simple intro
        # make contribution

        raise NotImplementedError
