import imghdr
import logging
import re
from argparse import ArgumentError, ArgumentParser
from pathlib import Path
from typing import Union

import eyed3
import eyed3.id3
from tqdm import tqdm

from . import xsession


class Downloader:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    @staticmethod
    def _validate_filename(s: str) -> str:
        s = re.sub(r"[/\\\\:*?\"<>|]", "_", s).strip()
        return s

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.s = xsession.KuwoMusic()
        self.s.headers.update(self.headers)

    def download_song(self, song_id, output_dir: Union[str, Path], metadata: bool = True, lyric: bool = True) -> bool:
        song_data = self.s.get_song_data(song_id)
        song_info = self.s.get_music_info(song_id)

        if song_data and song_info:
            song_name = self._validate_filename(song_info.get("name", "unknown"))
            save_path = Path(
                output_dir,
                "{} - {}.mp3".format(song_info.get("artist", "unknown"), song_name)
            )
            save_path.write_bytes(song_data)
        else:
            return False

        if metadata:
            song_eyed3 = eyed3.load(save_path.as_posix(), tag_version=eyed3.id3.ID3_V2)
            if song_eyed3.tag is None:
                song_eyed3.initTag()
            song_tag: eyed3.id3.Tag = song_eyed3.tag
            song_tag.title = song_info.get("name", "")
            song_tag.artist = song_info.get("artist", "")
            song_tag.album = song_info.get("album", "")
            # try add cover image
            res = self.s.get(song_info.get("pic", ""))
            if res.status_code == 200:
                cover_img = res.content
                song_tag.images.set(
                    eyed3.id3.frames.ImageFrame.FRONT_COVER,
                    cover_img,
                    "image/{}".format(imghdr.what(None, cover_img[:32]))
                )
            song_tag.save(encoding="utf8", version=eyed3.id3.ID3_V2_3)  # MUST be v2.3 to show cover image

        if lyric:
            ...

        return True

    def download_artist(self):
        raise NotImplementedError

    def download_album(self):
        raise NotImplementedError

    def download_playlist(self):
        raise NotImplementedError


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output_dir", default="kw_output")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--song", nargs="+")
    group.add_argument("--artist", nargs="+")
    group.add_argument("--album", nargs="+")
    group.add_argument("--playlist", nargs="+")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloader = Downloader()
    if args.song:
        for id_ in args.song:
            downloader.download_song(id_, output_dir)
    elif args.artist:
        print("Artist", args.artist)
    elif args.album:
        print("Album", args.album)
    elif args.playlist:
        print("Playlist", args.playlist)
    else:
        raise ArgumentError("No arguments specified.")
