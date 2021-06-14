# -*- coding: UTF-8 -*-

import imghdr
import json
from pathlib import Path
from typing import List, Union

import bs4

from .base import XSession


class Bilibili(XSession):
    url_host = "https://www.bilibili.com/"

    dynamic_svr_create = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create"
    dynamic_svr_create_draw = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/create_draw"
    dynamic_svr_rm_dynamic = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/rm_dynamic"

    drawImage_upload = "https://api.vc.bilibili.com/api/v1/drawImage/upload"

    def __init__(self, logfile=None, interval: float = 0.1, cookies: dict = None) -> None:
        super().__init__(logfile=logfile, interval=interval)
        if cookies:
            for name, value in cookies.items():
                self.cookies.set(name, value, domain="bilibili.com", path="/")
        # print(cookies)

    def _get_csrf(self) -> str:
        return self.cookies.get("bili_jct", default="")

    def _post_upload(self, img_path: Union[str, Path]) -> dict:
        """Upload a image and get url on static server

        Args:
            image_path: local image file path

        Returns:
            {
                "code": 0,
                "message": "success",
                "data": {
                    "image_url": "xxx",
                    "image_width": 625,
                    "image_height": 477
                }
            }
        """
        img_path = Path(img_path)
        with img_path.open("rb") as f:
            res = self.post(
                self.drawImage_upload,
                files={
                    "file_up": (img_path.name, f, "image/{}".format(imghdr.what(f))),
                    "biz": (None, "draw"),
                    "category": (None, "daily")
                }
            )

        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        return res.json().get("data")

    def post_create(self, content: str,
                    dynamic_id=0, type_=4, rid=0,
                    up_choose_comment=0, up_close_comment=0,
                    at_uids="", extension=None, ctrl=None) -> dict:
        """Create a dynamic

        Args:
            content: content for the dynamic

        Returns:
            If succeeded, return info about dynamic.

            {
                "code": 0,
                "msg": "",
                "message": "",
                "data": {
                    "result": 0,
                    "errmsg": "xxx",
                    "dynamic_id": xxx,
                    "create_result": 1,
                    "dynamic_id_str": "xxx",
                    "_gt_": 0
                }
            }
        """
        res = self.post(
            self.dynamic_svr_create,
            data={
                "content": content,
                "up_choose_comment": up_choose_comment,
                "up_close_comment": up_close_comment,
                "dynamic_id": dynamic_id,
                "type": type_,
                "rid": rid,
                "at_uids": at_uids,
                "ctrl": json.dumps([]),
                "extension": json.dumps({
                    "emoji_type": 1,
                    "from": {"emoji_type": 1},
                    "flag_cfg": {}
                }),
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            })

        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        return res.json().get("data")

    def post_create_draw(self, content: str, pictures: List[Union[str, Path]],
                         description: str = "", title: str = "", tags: str = "",
                         biz=3, category=3, type_=0,
                         at_uids="", from_="create.dynamic.web",
                         up_choose_comment=0, up_close_comment=0,
                         extension=None, setting=None, at_control=None):
        """Create dynamic with pictures

        Args:
            content: main content
            pictures: local paths of pictures needed to create with dynamic
            title:
            description: 
            tags:

        Returns:
            {
                "code": 0,
                "msg": "",
                "message": "",
                "data": {
                    "doc_id": "xxx",
                    "dynamic_id": xxx,
                    "dynamic_id_str": "xxx",
                    "_gt_": 0
                }
            }
        """
        res_pics = []
        # upload pictures
        for pic_path in map(Path, pictures):
            pic_info = self._post_upload(pic_path)
            if pic_info:
                res_pics.append({
                    "img_src": pic_info.get("image_url"),
                    "img_width": pic_info.get("image_width"),
                    "img_height": pic_info.get("image_height"),
                    "img_size": pic_path.stat().st_size / 1024
                })

        res = self.post(
            self.dynamic_svr_create_draw,
            data={
                "content": content,
                "pictures": json.dumps(res_pics),
                "title": title,
                "description": description or content,
                "category": category,
                "tags": tags,
                "up_choose_comment": up_choose_comment,
                "up_close_comment": up_close_comment,
                "biz": biz,
                "type": type_,
                "from": from_,
                "at_uids": at_uids,
                "at_control": json.dumps([]),
                "setting": json.dumps({
                    "copy_forbidden": 0,
                    "cachedTime": 0
                }),
                "extension": json.dumps({
                    "emoji_type": 1,
                    "from": {"emoji_type": 1},
                    "flag_cfg": {}
                }),
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            }
        )
        print(res.text)
        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        return res.json().get("data")

    def post_rm_dynamic(self, dynamic_id) -> dict:
        """Delete a dynamic"""
        res = self.post(
            self.dynamic_svr_rm_dynamic,
            data={
                "dynamic_id": dynamic_id,
                "csrf": self._get_csrf(),
                "csrf_token": self._get_csrf()
            }
        )
        if res.status_code != 200 or res.json().get("code") != 0:
            return {}
        else:
            return res.json().get("data")
