import logging
from os import PathLike, sep
from pathlib import Path

from utils import media, xsession
from utils.miragetank import MirageTank


class PixivDrive:
    proxies = {
        "http": "http://127.0.0.1:10809",
        "https": "http://127.0.0.1:10809"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
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

    def upload_illust(self, illust_id: str, mirage_cover_path: PathLike = None) -> bool:
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
            mirage_cover_path (PathLike): When supported, if illust is R18, 
                will also upload mirage version using this image as cover
        """

        illust_info = self.s_pixiv.get_illust(illust_id)

        if not illust_info:
            return False

        user_id = illust_info["userId"]
        username = illust_info["userName"]

        # root_dir/user_id
        user_dir = self.root_dir.joinpath(user_id)

        # use a folder to record current username
        self.s_adrive.create_folder(user_dir.joinpath(username))

        # tmp download folder
        # tmp/illust_id
        illust_local_save_folder = Path("tmp", illust_id)
        illust_local_save_folder.mkdir(parents=True, exist_ok=True)

        # tmp/illust_id/page_p0.png
        page_local_paths = self.s_pixiv.download_illust(illust_id, illust_local_save_folder)

        # if is R18, upload extra mirage version

        if not page_local_paths:
            return False

        # add salt to avoid same hash
        for path in page_local_paths:
            if not media.img_add_salt(path):
                self.logger.warning("Failed to add salt to page {}, upload original page.".format(path.as_posix()))
            self.s_adrive.upload_file(
                user_dir.joinpath(illust_id, path.name),
                path,
                check_name_mode="overwrite"
            )

        # if is R18, make mirage version
        if illust_info["xRestrict"] and mirage_cover_path:
            # DEBUG
            print("R18:", illust_id, sep="", end=";", flush=True)
            # DEBUG
            self.logger.info("Try make mirage for illust {}.".format(illust_id))
            illust_mirage_local_save_folder = Path("tmp", "{}_mirage".format(illust_id))
            illust_mirage_local_save_folder.mkdir(parents=True, exist_ok=True)

            # make mirage and upload
            for path in page_local_paths:
                save_path = illust_mirage_local_save_folder.joinpath(path.name)
                save_path = MirageTank.make_mirage(mirage_cover_path, path, save_path)
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
        include_user_top: bool = False,
        mirage_cover_path: PathLike = None
    ) -> bool:
        """Upload pixiv monthly ranking illusts.

        Args:
            include_user_top (bool): Whether to upload top illusts of users in ranking as well.
        """
        print("##### DEBUG 0 BEGIN #####", flush=True)
        ranking_info = self.s_pixiv.get_ranking_monthly()
        print("\n##### DEBUG 0 END #####", flush=True)
        if not ranking_info:
            return False

        # upload ranking illusts
        illust_ids = [str(e["illust_id"]) for e in ranking_info["contents"]]
        flag = True
        print("##### DEBUG 1 BEGIN #####", flush=True)
        for id_ in illust_ids:
            # print(id_, end=";", flush=True)
            if not self.upload_illust(id_):
                flag = False
        print("\n##### DEBUG 1 END #####", flush=True)

        if not flag:
            self.logger.warning("Failed to upload some illusts.")

        # upload users in ranking top illusts
        if include_user_top:
            illust_ids = set()
            user_ids = [e["user_id"] for e in ranking_info["contents"]]
            print("##### DEBUG 2 BEGIN #####", flush=True)
            for id_ in user_ids:
                print(id_, end=";", flush=True)
                top_info = self.s_pixiv.get_user_top(id_)
                if top_info:
                    for illust_id in top_info["illusts"].keys():
                        illust_ids.add(str(illust_id))
            print("\n##### DEBUG 2 END #####", flush=True)

            flag = True
            print("##### DEBUG 3 BEGIN #####", flush=True)
            print("Num: ", len(illust_ids), flush=True)
            for id_ in illust_ids:
                # print(id_, end=";", flush=True)
                if not self.upload_illust(id_, mirage_cover_path):
                    flag = False
            print("\n##### DEBUG 3 END #####", flush=True)
            if not flag:
                self.logger.warning("Failed to upload some user top illusts.")

        return True
