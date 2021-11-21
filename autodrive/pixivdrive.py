from os import PathLike
from utils import media, xsession
from pathlib import Path
import logging


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

    def upload_illust(self, illust_id: str) -> bool:
        """Upload a illust to root_dir.

        The directory tree may like this:
            <root_dir>/
                <user_id - username>
                    <illust_id>
                        <illust_id_p0>
                        <illust_id_p1>
                        ...
                    <illust_id>
                        ...
                <artist_id>
                    ...
        """

        illust_info = self.s_pixiv.get_illust(illust_id)

        if illust_info:
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

            if page_local_paths:
                # add salt to avoid same hash
                for path in page_local_paths:
                    if not media.img_add_salt(path):
                        self.logger.warning("Failed to add salt to page {}, upload original page.".format(path.as_posix()))
                    self.s_adrive.upload_file(user_dir.joinpath(illust_id, path.name), path, check_name_mode="overwrite")

                return True

        return False

    def upload_monthly_ranking(self, *, include_user_top: bool = False) -> bool:
        """Upload pixiv monthly ranking illusts.

        Args:
            include_user_top (bool): Whether to upload top illusts of users in ranking as well.
        """

        ranking_info = self.s_pixiv.get_ranking_monthly()

        if not ranking_info:
            return False

        # upload ranking illusts
        illust_ids = [str(e["illust_id"]) for e in ranking_info["contents"]]
        flag = True
        for id_ in illust_ids:
            if not self.upload_illust(id_):
                flag = False

        if not flag:
            self.logger.warning("Failed to upload some illusts.")

        # upload users in rannking top illusts
        if include_user_top:
            illust_ids = set()
            user_ids = [e["user_id"] for e in ranking_info["contents"]]
            for id_ in user_ids:
                top_info = self.s_pixiv.get_user_top(id_)
                if top_info:
                    for illust_id in top_info["illusts"].keys():
                        illust_ids.add(str(illust_id))

            flag = True
            for id_ in illust_ids:
                if not self.upload_illust(id_):
                    flag = False
            if not flag:
                self.logger.warning("Failed to upload some user top illusts.")

        return True
