import json
import logging
import random
from os import PathLike
from pathlib import Path
import re
import shutil

from utils import media, xsession


class PixivDrive:
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0"
    }

    def __init__(self, root_dir: PathLike = "pixiv") -> None:
        """
        Args:
            root_dir (PathLike): The root working directory.
        """
        self.logger = logging.getLogger(__name__)

        self.s_adrive = xsession.AliyunDrive()
        self.s_pixiv = xsession.Pixiv()
        self.s_adrive.headers.update(self.headers)
        self.s_pixiv.headers.update(self.headers)

        # # DEBUG
        # self.s_pixiv.proxies.update(self.proxies)

        self.root_dir = Path(root_dir)

    def login(self, *, refresh_token: str = "",  p_cookies: dict = None) -> bool:
        """Login.

        Args:
            refresh_token (str): refresh_token used to login aliyundrive.
            p_cookies (dict): cookies used to login pixiv.
        """

        if not refresh_token:
            self.logger.error("Failed to login aliyundrive.")
            return False

        if not self.s_adrive.login("", "", refresh_token=refresh_token):
            self.logger.error("Failed to login aliyundrive.")
            return False

        if not p_cookies:
            self.logger.warning("Pixiv not login, some api may be restricted.")
        else:
            self.s_pixiv.cookies.update(p_cookies)
            self.logger.info("Pixiv cookies used.")

        self.logger.info("Login success.")
        return True

    def upload_illust(self, illust_id: str) -> bool:
        """Upload a illust to root_dir.

        The directory tree may like this:
            <root_dir>/
                <user_id>
                    <user_name>
                    <illust_id>
                        <illust_id_p0>
                        <illust_id_p1>
                        ...
                    <illust_id_mirage>
                        ...
                    <illust_id>
                        ...
                    ...

        Args:
            illust_id (str): illust id

        Note: 
            will use blacktank for R18
        """

        illust_info = self.s_pixiv.get_illust(illust_id)

        if not illust_info:
            return False

        user_id = illust_info["userId"]
        username = illust_info["userName"]

        # root_dir/user_id
        user_dir = self.root_dir.joinpath(user_id)

        # use a folder to record current username
        self.s_adrive.create_folder(user_dir.joinpath(f"{username} - {user_id}"))

        # tmp download folder
        # tmp/illust_id
        illust_local_save_folder = Path("tmp", illust_id)
        illust_local_save_folder.mkdir(parents=True, exist_ok=True)

        # upload illust info json file
        illust_info_local_save_path = illust_local_save_folder.joinpath(f"{illust_id}.json.txt")
        illust_info_local_save_path.write_text(json.dumps(illust_info, ensure_ascii=False, indent=4), encoding="utf8")
        self.s_adrive.upload_file(
            user_dir.joinpath(illust_id, illust_info_local_save_path.name),
            illust_info_local_save_path,
            check_name_mode="overwrite"
        )

        # tmp/illust_id/page_p0.png
        page_local_paths = self.s_pixiv.download_illust(illust_id, illust_local_save_folder)

        # upload pages
        # if is R18, upload extra mirage version

        if not page_local_paths:
            return False

        # add salt to avoid same hash
        for path in page_local_paths:
            if not media.img_add_salt(path, random_salt=True):
                self.logger.warning("Failed to add salt to page {}, upload original page.".format(path.as_posix()))
            self.s_adrive.upload_file(
                user_dir.joinpath(illust_id, path.name),
                path,
                check_name_mode="overwrite"
            )

        # if is R18, make mirage version
        if illust_info["xRestrict"]:
            # # DEBUG
            # print("R18:", illust_id, sep="", end=";", flush=True)
            # # DEBUG
            self.logger.info("Try make mirage for illust {}.".format(illust_id))
            illust_mirage_local_save_folder = Path("tmp", "{}_mirage".format(illust_id))
            illust_mirage_local_save_folder.mkdir(parents=True, exist_ok=True)

            # make mirage and upload
            for path in page_local_paths:
                save_path = illust_mirage_local_save_folder.joinpath(path.name)
                save_path = media.make_blacktank(path, save_path)

                if save_path:
                    self.s_adrive.upload_file(
                        user_dir.joinpath("{}_mirage".format(illust_id), save_path.name),
                        save_path,
                        check_name_mode="overwrite"
                    )
                else:
                    self.logger.warning("Failed to make mirage for page {}.".format(path.as_posix()))

        return True

    def upload_monthly_ranking(
        self,
        *,
        include_user_top: bool = False
    ) -> bool:
        """Upload pixiv monthly ranking illusts.

        Args:
            include_user_top (bool): Whether to upload top illusts of users in ranking as well.
        """
        # print("##### DEBUG 0 BEGIN #####", flush=True)
        ranking_info = self.s_pixiv.get_ranking_monthly()
        # print("\n##### DEBUG 0 END #####", flush=True)
        if not ranking_info:
            return False

        # upload ranking illusts
        illust_ids = [str(e["illust_id"]) for e in ranking_info["contents"]]
        flag = True
        # print("##### DEBUG 1 BEGIN #####", flush=True)
        for id_ in illust_ids:
            # print(id_, end=";", flush=True)
            if not self.upload_illust(id_):
                flag = False
        # print("\n##### DEBUG 1 END #####", flush=True)

        if not flag:
            self.logger.warning("Failed to upload some illusts.")

        # upload users in ranking top illusts
        if include_user_top:
            illust_ids = set()
            user_ids = [e["user_id"] for e in ranking_info["contents"]]
            # print("##### DEBUG 2 BEGIN #####", flush=True)
            for id_ in user_ids:
                # print(id_, end=";", flush=True)
                top_info = self.s_pixiv.get_user_top(id_)
                if top_info:
                    for illust_id in top_info["illusts"].keys():
                        illust_ids.add(str(illust_id))
            # print("\n##### DEBUG 2 END #####", flush=True)

            # shuffle
            illust_ids = list(illust_ids)
            for _ in range(1000):
                random.shuffle(illust_ids)
            # limit to 500 illust ids
            # illust_ids = illust_ids[:500]

            # print("##### DEBUG 3 BEGIN #####", flush=True)
            # print(illust_ids)
            # print("Num: ", len(illust_ids), flush=True)

            flag = True
            for id_ in illust_ids:
                # print(id_, end=";", flush=True)
                if not self.upload_illust(id_):
                    flag = False
            # print("\n##### DEBUG 3 END #####", flush=True)
            if not flag:
                self.logger.warning("Failed to upload some user top illusts.")

        return True

    def check_illust_info_json(self) -> bool:
        """Used to upload missing `illust_info.json.txt` files."""

        for user_folder in self.s_adrive.glob_file("", file_drive_path=self.root_dir):
            user_id = user_folder["name"]
            for illust_folder in self.s_adrive.glob_file(user_folder["file_id"]):
                # check if exist <illust_id>.json.txt
                illust_id: str = illust_folder["name"]

                # check valid illust folder
                if not re.search(r"^[0-9]*$", illust_id):
                    continue

                illust_info_filename = f"{illust_id}.json.txt"
                for file in self.s_adrive.glob_file(illust_folder["file_id"]):
                    if file["name"] == illust_info_filename and file["size"] > 1024:
                        break  # already exist
                else:
                    # upload info json
                    print(f"Try append illust {illust_id} info json")
                    illust_info = self.s_pixiv.get_illust(illust_id)
                    if not illust_info:
                        self.logger.warning(f"Failed to get illust {illust_id} info, skip it.")
                        continue

                    local_save_path = Path("tmp", user_id, illust_id, illust_info_filename)
                    local_save_path.parent.mkdir(parents=True, exist_ok=True)
                    local_save_path.write_text(json.dumps(illust_info, ensure_ascii=False, indent=4), encoding="utf8")
                    self.s_adrive.upload_file(
                        illust_info_filename,
                        local_save_path,
                        illust_folder["file_id"],
                        check_name_mode="overwrite"
                    )

        return True

    def clean_dateset(self, dataset_dir: PathLike, *, add_user_all: bool = False):
        """Check and clean dataset downloaded in drive. 
        Will try to download missing illusts and remove unavailable folders and illusts.

        Args:
            dataset_dir: the dataset root dir., may like `~/pixiv`.
            add_user_all: whether add user all illusts.
        """

        for user_folder in Path(dataset_dir).iterdir():
            user_id = user_folder.name
            if add_user_all:
                user_all_info = self.s_pixiv.get_user_all(user_id)
                if not user_all_info:
                    self.logger.warning(f"Failed to add user {user_id} all illusts, skip.")
                else:
                    for illust_id in user_all_info["illusts"]:
                        self.s_pixiv.download_illust(illust_id, user_folder.joinpath(illust_id))

            # check illusts
            for illust_folder in user_folder.iterdir():
                # check if exist <illust_id>.json.txt
                illust_id = illust_folder.name

                # delete invalid folder
                if not re.search(r"^[0-9]*$", illust_id):
                    shutil.rmtree(illust_folder)
                # check files all existed and download them
                else:
                    # check info json file
                    info_json_file = illust_folder.joinpath(f"{illust_id}.json.txt")
                    if not info_json_file.is_file() or info_json_file.stat().st_size <= 1024:
                        illust_info = self.s_pixiv.get_illust(illust_id)
                        if not illust_info:
                            self.logger.error(f"Failed to get {info_json_file}, json info file save error.")
                            continue
                        # save info file
                        info_json_file.write_text(json.dumps(illust_info, ensure_ascii=False, indent=4), encoding="utf8")

                    # check illust pages
                    paths = self.s_pixiv.download_illust(illust_id, illust_folder)
                    if len(paths) <= 0:
                        self.logger.error(f"Illust folder {illust_folder} has no illust downloaded, try to remove it manually.")
                        continue
