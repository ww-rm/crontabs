# -*- coding: UTF-8 -*-

import json
from os import PathLike
from pathlib import Path
from typing import Any, Iterator, Union
import bs4
import requests
from .base import XSession, empty_retry


class PixivBase(XSession):
    # lang=zh
    url_host = "https://www.pixiv.net"

    # api
    api_login = "https://accounts.pixiv.net/api/login"

    # ajax

    ajax_top_illust = "https://www.pixiv.net/ajax/top/illust"  # ?mode=all|r18 # many many info in index page

    ajax_search_tags = "https://www.pixiv.net/ajax/search/tags/{keyword}"
    # ?order=date&mode=all&p=1&s_mode=s_tag # param for url_search_*
    ajax_search_artworks = "https://www.pixiv.net/ajax/search/artworks/{keyword}"
    ajax_search_illustrations = "https://www.pixiv.net/ajax/search/illustrations/{keyword}"  # ?type=illust
    ajax_search_manga = "https://www.pixiv.net/ajax/search/manga/{keyword}"

    ajax_user = "https://www.pixiv.net/ajax/user/{user_id}"  # user simple info
    ajax_user_following = "https://www.pixiv.net/ajax/user/{user_id}/following"  # ?offset=0&limit=24&rest=show
    ajax_user_recommends = "https://www.pixiv.net/ajax/user/{user_id}/recommends"  # ?userNum=20&workNum=3&isR18=true
    ajax_user_profile_all = "https://www.pixiv.net/ajax/user/{user_id}/profile/all"  # user all illusts and details # 9930155
    ajax_user_profile_top = "https://www.pixiv.net/ajax/user/{user_id}/profile/top"
    ajax_user_illusts = "https://www.pixiv.net/ajax/user/{user_id}/illusts"  # ?ids[]=84502979"

    ajax_illust = "https://www.pixiv.net/ajax/illust/{illust_id}"  # illust details # 70850475
    ajax_illust_pages = "https://www.pixiv.net/ajax/illust/{illust_id}/pages"  # illust pages
    ajax_illust_recommend_init = "https://www.pixiv.net/ajax/illust/{illust_id}/recommend/init"  # limit=1

    ajax_illusts_like = "https://www.pixiv.net/ajax/illusts/like"  # illust_id:""
    ajax_illusts_bookmarks_add = "https://www.pixiv.net/ajax/illusts/bookmarks/add"  # comment:"" illust_id:"" restrict:0 tags:[]

    # php
    php_logout = "https://www.pixiv.net/logout.php"  # ?return_to=%2F
    php_ranking = "https://www.pixiv.net/ranking.php"  # ?format=json&p=1&mode=daily&content=all
    php_rpc_recommender = "https://www.pixiv.net/rpc/recommender.php"  # ?type=illust&sample_illusts=88548686&num_recommendations=500
    php_bookmark_add = "https://www.pixiv.net/bookmark_add.php"  # mode:"add" type:"user" user_id:"" tag:"" restrict:"" format:"json"

    def _check_response(self, res: requests.Response) -> Union[dict, list]:
        """Check response."""

        if res.status_code is None:
            return {}

        try:
            json_ = res.json()
        except ValueError:
            self.logger.error("{}:JsonValueError.".format(res.url))
            return {}

        if json_["error"] is True:
            self.logger.error("{}:{}".format(
                res.url,
                json_.get("message", "") or json_.get("msg", "No msg.")
            ))
            return {}
        return json_["body"]

    def _check_response2(self, res: requests.Response) -> Union[dict, list]:
        """Check response."""

        if res.status_code is None:
            return {}

        try:
            json_ = res.json()
        except ValueError:
            self.logger.error("{}:JsonValueError.".format(res.url))
            return {}

        if "error" in json_:
            self.logger.error("{}:{}".format(res.url, json_["error"]))
            return {}
        return json_

    def __init__(self, interval: float = 0.01) -> None:
        super().__init__(interval=interval)
        self.headers["Referer"] = PixivBase.url_host

    def _get_csrf_token(self) -> str:
        """Get x-csrf-token"""
        html = self.get(PixivBase.url_host).text
        soup = bs4.BeautifulSoup(html, "lxml")
        token = json.loads(soup.find("meta", {"id": "meta-global-data"}).attrs.get("content", "{}")).get("token", "")
        return token

    # GET method

    @empty_retry()
    def _get_page(self, page_url: str, chunk_size: int = 10485760) -> Iterator[bytes]:
        """
        Args:
            page_url (str): url to get page from.
            chunk_size (str): To avoid huge memory usage, default to 10 MB.

        Returns:
            Return empty bytes when failed, otherwise a bytes iterator.
        """
        res = self.get(page_url, stream=True)
        if res.status_code != 200:
            self.logger.error("Failed to get page from {}.".format(page_url))
            return b""  # Need to make bool False
        return res.iter_content(chunk_size)

    def _get_top_illust(self, mode="all") -> dict:
        """Get top illusts by mode.

        Args:
            mode: "all" means all ages, "r18" means R-18 only
        """
        res = self.get(
            PixivBase.ajax_top_illust,
            params={"mode": mode}
        )
        return self._check_response(res)

    def _get_search_artworks(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="all") -> dict:
        """Get search artworks result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: No need to care
        """
        res = self.get(
            PixivBase.ajax_search_artworks.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }
        )
        return self._check_response(res)

    def _get_search_illustrations(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="illust") -> dict:
        """Get search illustration or ugoira result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: "illust", "ugoira", "illust_and_ugoira"
        """
        res = self.get(
            PixivBase.ajax_search_illustrations.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }
        )
        return self._check_response(res)

    def _get_search_manga(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="manga") -> dict:
        """Get search manga result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: No need to care
        """
        res = self.get(
            PixivBase.ajax_search_manga.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }
        )
        return self._check_response(res)

    @empty_retry()
    def _get_illust(self, illust_id) -> dict:
        res = self.get(
            PixivBase.ajax_illust.format(illust_id=illust_id)
        )

        return self._check_response(res)

    def _get_illust_pages(self, illust_id) -> list:
        res = self.get(
            PixivBase.ajax_illust_pages.format(illust_id=illust_id)
        )
        return self._check_response(res)

    def _get_illust_recommend_init(self, illust_id, limit=1) -> dict:
        """details.keys()"""
        res = self.get(
            PixivBase.ajax_illust_recommend_init.format(illust_id=illust_id),
            params={"limit": limit}
        )
        return self._check_response(res)

    def _get_user(self, user_id) -> dict:
        res = self.get(
            PixivBase.ajax_user.format(user_id=user_id)
        )

        return self._check_response(res)

    def _get_user_following(self, user_id, offset, limit=50, rest="show") -> dict:
        """Get following list of a user

        Args:
            offset: Start index of list
            limit: Number of list, default to "50", must < 90
            rest(restrict): "show" means "public", "hide" means private, you can just see private followings for your own account

        Returns:
            The list is body.users
        """
        res = self.get(
            PixivBase.ajax_user_following.format(user_id=user_id),
            params={
                "offset": offset,
                "limit": min(limit, 90),
                "rest": rest
            }
        )
        return self._check_response(res)

    def _get_user_recommends(self, user_id, userNum=100, workNum=3, isR18=True) -> dict:
        """Get recommends of a user

        Args:
            userNum: Number of recommends' user, limit to less than 100
            workNum: Unknown
            isR18: Unknown

        Returns:
            Recommends list is body.recommendUsers, the length of list <= userNum
        """
        res = self.get(
            PixivBase.ajax_user_recommends.format(user_id=user_id),
            params={
                "userNum": userNum,
                "workNum": workNum,
                "isR18": isR18
            }
        )
        return self._check_response(res)

    def _get_user_profile_all(self, user_id) -> dict:
        res = self.get(PixivBase.ajax_user_profile_all.format(user_id=user_id))
        return self._check_response(res)

    def _get_user_profile_top(self, user_id) -> dict:
        res = self.get(PixivBase.ajax_user_profile_top.format(user_id=user_id))
        return self._check_response(res)

    @empty_retry()
    def _get_ranking(self, p=1, content="all", mode="daily", date: str = None) -> dict:
        """Get ranking, limit 50 illusts info in one page

        Args:
            p: page number, >= 1
            content: 
                "all": mode[Any]
                "illust": mode["daily", "weekly", "daily_r18", "weekly_r18", "monthly", "rookie"]
                "ugoira"(動イラスト): mode["daily", "weekly", "daily_r18", "weekly_r18"]
                "manga": mode["daily", "weekly", "daily_r18", "weekly_r18", "monthly", "rookie"]
            mode: ["daily", "weekly", "daily_r18", "weekly_r18", "monthly", "rookie", 
                "original", "male", "male_r18", "female", "female_r18"]
            date: ranking date, example: 20210319, None means the newest

        Note: 
            May need cookies to get r18 ranking.
        """
        res = self.get(
            PixivBase.php_ranking,
            params={"format": "json", "p": p, "content": content, "mode": mode, "date": date}
        )

        return self._check_response2(res)

    def _get_logout(self) -> bool:
        """Logout"""
        res = self.get(PixivBase.php_logout, params={"return_to": "/"})
        return True

    # POST method

    def _post_login(self, usrn, pwd, source="pc") -> bool:
        # TODO: captcha arguments
        raise NotImplementedError

    def _post_illusts_bookmarks_add(self, illust_id, restrict: int = 0, comment: str = "", tags: list = None) -> bool:
        """Add or modify bookmark of an illust

        Args:
            illust_id: illust id
            restrict: 0 for public, 1 for private
            comment: comment
            tags: a list contains string tags, can be empty list
        """

        res = self.post(
            PixivBase.ajax_illusts_bookmarks_add,
            json={
                "illust_id": illust_id,
                "restrict": restrict,
                "comment": comment,
                "tags": tags
            },
            headers={
                "x-csrf-token": self._get_csrf_token()  # 400
            }
        )
        return self._check_response2(res)

    def _post_bookmark_add(self, user_id, restrict=0, tag="", mode="add", type_="user") -> bool:
        """Add or modify bookmark of a user

        Args:
            user_id: user id
            restrict: 0 for public, 1 for private
            tag: Unknown
            mode: No need to care
            type_: No need to care
        """
        res = self.post(
            PixivBase.php_bookmark_add,
            data={
                "user_id": user_id,
                "restrict": restrict,
                "tag": tag,
                "mode": mode,
                "type": type_,
                "format": "json"
            },
            headers={
                "x-csrf-token": self._get_csrf_token()  # 404
            }
        )
        return False if res.status_code != 200 else True


class Pixiv(PixivBase):
    """"""

    def download_page(self, page_url: str, page_save_path: PathLike) -> bool:
        """Download a single page."""

        data = self._get_page(page_url)

        if not data:
            self.logger.error("Failed to download page {}.".format(page_url))
            return False

        with Path(page_save_path).open("wb") as f:
            for chunk in data:
                f.write(chunk)
        return True

    def download_illust(self, illust_id: str, illust_save_folder: Path) -> bool:
        """"""
        raise NotImplementedError

    def get_illust(self, illust_id: str) -> dict:
        """Get illust info."""

        illust_info = self._get_illust(illust_id)

        if not illust_info:
            self.logger.error("Failed to get {} illust info.".format(illust_id))
            return {}
        return illust_info

    def get_ranking_daily(self, p: int = 1, content: str = "illust", date: str = None, r18: bool = False) -> dict:
        """Get daily ranking info.

        Args:
            p: page num, each page has 50 records.
            content: ["all" | "illust" | "ugoira" | "manga"]
            date: None means newest, or like "20120814".
            r18: Whether only return r18, need to login.
        """

        mode = "daily_r18" if r18 else "daily"
        ranking_info = self._get_ranking(p, content, mode, date)
        if not ranking_info:
            self.logger.error("Failed to get daily ranking info {}:{}:{}:{}.".format(p, content, date, r18))
            return {}
        return ranking_info

    def get_ranking_weekly(self, p: int = 1, content: str = "illust", date: str = None, r18: bool = False) -> dict:
        """Get weekly ranking info.

        Args:
            p: page num, each page has 50 records.
            content: ["all" | "illust" | "ugoira" | "manga"]
            date: None means newest, or like "20120814".
            r18: Whether only return r18, need to login.
        """

        mode = "weekly_r18" if r18 else "weekly"
        ranking_info = self._get_ranking(p, content, mode, date)
        if not ranking_info:
            self.logger.error("Failed to get weekly ranking info {}:{}:{}:{}.".format(p, content, date, r18))
            return {}
        return ranking_info

    def get_ranking_monthly(self, p: int = 1, content: str = "illust", date: str = None) -> dict:
        """Get monthly ranking info.

        Args:
            p: page num, each page has 50 records.
            content: ["all" | "illust" | "manga"]
            date: None means newest, or like "20120814".
        """

        ranking_info = self._get_ranking(p, content, "monthly", date)
        if not ranking_info:
            self.logger.error("Failed to get monthly ranking info {}:{}:{}.".format(p, content, date))
            return {}
        return ranking_info
