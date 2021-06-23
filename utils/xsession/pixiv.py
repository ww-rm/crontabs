# -*- coding: UTF-8 -*-

import json
import bs4
from .base import XSession


class Pixiv(XSession):
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

    def __init__(self, interval: float = 0.1, cookies: dict = None) -> None:
        super().__init__(interval=interval)
        self.headers["Referer"] = self.url_host
        if cookies:
            for name, value in cookies.items():
                self.cookies.set(name, value, domain=".pixiv.net", path="/")
        # print(self.cookies)

    def _get_csrf_token(self) -> str:
        """Get x-csrf-token"""
        html = self.get(self.url_host).text
        soup = bs4.BeautifulSoup(html, "lxml")
        token = json.loads(soup.find("meta", {"id": "meta-global-data"}).attrs.get("content")).get("token")
        return token

    # GET method

    def get_page(self, page_url) -> bytes:
        response = self.get(page_url)
        if response.status_code != 200:
            return b""
        return response.content

    def get_top_illust(self, mode="all") -> dict:
        """Get top illusts by mode

        Args:
            mode: "all" means all ages, "r18" means R-18 only
        """
        json_ = self.get(self.ajax_top_illust, params={"mode": mode}).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_search_artworks(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="all") -> dict:
        """Get search artworks result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: No need to care
        """
        json_ = self.get(
            self.ajax_search_artworks.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_search_illustrations(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="illust") -> dict:
        """Get search illustration or ugoira result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: "illust", "ugoira", "illust_and_ugoira"
        """
        json_ = self.get(
            self.ajax_search_illustrations.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_search_manga(self, keyword, order="date_d", mode="all", p=1, s_mode="s_tag", type_="manga") -> dict:
        """Get search manga result

        Args:
            order: "date" means date ascend, "date_d" means date descend
            mode: "all", "safe", "r18"
            p: search result page
            s_mode: "s_tag" partly match tag, "s_tag_full" exactly match tag, "s_tc" match title and character description
            type_: No need to care
        """
        json_ = self.get(
            self.ajax_search_manga.format(keyword=keyword),
            params={
                "order": order,
                "mode": mode,
                "p": p,
                "s_mode": s_mode,
                "type": type_
            }).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_illust(self, illust_id) -> dict:
        json_ = self.get(self.ajax_illust.format(illust_id=illust_id)).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_illust_pages(self, illust_id) -> list:
        json_ = self.get(self.ajax_illust_pages.format(illust_id=illust_id)).json()
        return [] if json_.get("error") is True else json_.get("body")

    def get_illust_recommend_init(self, illust_id, limit=1) -> dict:
        """details.keys()"""
        json_ = self.get(
            self.ajax_illust_recommend_init.format(illust_id=illust_id),
            params={"limit": limit}
        ).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_user(self, user_id) -> dict:
        json_ = self.get(self.ajax_user.format(user_id=user_id)).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_user_following(self, user_id, offset, limit=50, rest="show") -> dict:
        """Get following list of a user

        Args:
            offset: Start index of list
            limit: Number of list, default to "50", must < 90
            rest(restrict): "show" means "public", "hide" means private, you can just see private followings for your own account

        Returns:
            The list is body.users
        """
        json_ = self.get(
            self.ajax_user_following.format(user_id=user_id),
            params={"offset": offset, "limit": limit if limit < 90 else 90, "rest": rest}
        ).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_user_recommends(self, user_id, userNum=100, workNum=3, isR18=True) -> dict:
        """Get recommends of a user

        Args:
            userNum: Number of recommends' user, limit to less than 100
            workNum: Unknown
            isR18: Unknown

        Returns:
            Recommends list is body.recommendUsers, the length of list <= userNum
        """
        json_ = self.get(
            self.ajax_user_recommends.format(user_id=user_id),
            params={"userNum": userNum, "workNum": workNum, "isR18": isR18}
        ).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_user_profile_all(self, user_id) -> dict:
        json_ = self.get(self.ajax_user_profile_all.format(user_id=user_id)).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_user_profile_top(self, user_id) -> dict:
        json_ = self.get(self.ajax_user_profile_top.format(user_id=user_id)).json()
        return {} if json_.get("error") is True else json_.get("body")

    def get_ranking(self, p=1, content="all", mode="daily", date: str = None) -> dict:
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

        Note: May need cookies to get r18 ranking
        """
        json_ = self.get(
            self.php_ranking,
            params={"format": "json", "p": p, "content": content, "mode": mode, "date": date}
        ).json()
        return {} if json_.get("error") else json_

    def get_rpc_recommender(self, sample_illusts: int, num_recommendations=500, type_="illust") -> list:
        """Deprecated, used to get recommended illust ids

        Args:
            sample_illusts: illust id
            num_recommendations: recommend illusts number
            type_: no need to care
        """
        json_ = self.get(
            self.php_rpc_recommender,
            params={
                "sample_illusts": sample_illusts,
                "num_recommendations": num_recommendations,
                "type": type_
            }
        ).json()
        return [] if json_.get("error") else json_.get("recommendations")

    def get_logout(self) -> bool:
        """Logout"""
        response = self.get(self.php_logout, params={"return_to": "/"})
        return True

    # POST method

    def post_login(self, usrn, pwd, source="pc") -> bool:
        # TODO: captcha arguments
        raise NotImplementedError

    def post_illusts_bookmarks_add(self, illust_id, restrict: int = 0, comment: str = "", tags: list = None) -> bool:
        """Add or modify bookmark of an illust

        Args:
            illust_id: illust id
            restrict: 0 for public, 1 for private
            comment: comment
            tags: a list contains string tags, can be empty list
        """

        json_ = self.post(
            self.ajax_illusts_bookmarks_add,
            json={
                "illust_id": illust_id,
                "restrict": restrict,
                "comment": comment,
                "tags": tags
            },
            headers={
                "x-csrf-token": self._get_csrf_token()  # 400
            }
        ).json()
        return False if json_.get("error") else True

    def post_bookmark_add(self, user_id, restrict=0, tag="", mode="add", type_="user") -> bool:
        """Add or modify bookmark of a user

        Args:
            user_id: user id
            restrict: 0 for public, 1 for private
            tag: Unknown
            mode: No need to care
            type_: No need to care
        """
        response = self.post(
            self.php_bookmark_add,
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
        return False if response.status_code != 200 else True
