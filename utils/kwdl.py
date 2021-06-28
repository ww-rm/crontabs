import imghdr
import logging
import re
from argparse import ArgumentError, ArgumentParser
from pathlib import Path
from typing import List, Tuple, Union

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

    def _get_lyric(self, song_id) -> List[Tuple[str, str]]:
        """
        Returns

        [(time, text), ...], time: "[mm:ss:ms]", text: "xxx"
        """
        def _cvt_time(t: str) -> str:
            t = float(t)
            s, ms = int(t), (t-int(t))*1000
            m, s = divmod(s, 60)
            return "[{:02d}:{:02d}.{:02d}]".format(m, s, int(ms/10))
        lyric_info = self.s.get_songinfo_and_lyric(song_id)
        lyrics = []
        if lyric_info:
            for e in lyric_info.get("lrclist"):
                lyrics.append((_cvt_time(e.get("time", "")), e.get("lineLyric")))
        else:
            self.logger.warning("Kuwo:Failed to get lyric:{}".format(song_id))
        return lyrics

    def download_song(self, song_id, output_dir: Union[str, Path], metadata: bool = True, lyric: bool = True) -> bool:
        """Download a song from kuwo

        Args

        song_id:
            song_id, you can get it from details page
        output_dir:
            output_dir
        metadata:
            whether save tag info of song, e.g. title, album, cover image
        lyric:
            whether save `.lrc` format lyrics to the output_dir
        """
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
            self.logger.error("Failed to get song:{}".format(song_id))
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
            lyrics = self._get_lyric(song_id)
            lyric_save_path = save_path.with_suffix(".lrc")
            with lyric_save_path.open("w", encoding="utf8") as f:
                for t, l in lyrics:
                    f.write("{}{}\n".format(t, l))

        return True

    def download_artist(self, artist_id, output_dir: Union[str, Path], metadata: bool = True, lyric: bool = True, num: int = 9999) -> int:
        song_ids = []
        cur_p = 1
        while len(song_ids) < num:
            artist_music = self.s.get_artist_music(artist_id, pn=cur_p)
            if not artist_music or not artist_music.get("list"):
                break
            song_ids.extend(e.get("rid") for e in artist_music.get("list"))

        success_count = 0
        for id_ in tqdm(song_ids[:num], "Artist:{}".format(artist_id)):
            if self.download_song(id_, output_dir, metadata, lyric):
                success_count += 1

        return success_count

    def download_album(self, album_id, output_dir: Union[str, Path], metadata: bool = True, lyric: bool = True, num: int = 9999) -> int:
        song_ids = []
        cur_p = 1
        while len(song_ids) < num:
            album_info = self.s.get_album_info(album_id, pn=cur_p)
            if not album_info or not album_info.get("musicList"):
                break
            song_ids.extend(e.get("rid") for e in album_info.get("musicList"))

        success_count = 0
        for id_ in tqdm(song_ids[:num], "Album:{}".format(album_id)):
            if self.download_song(id_, output_dir, metadata, lyric):
                success_count += 1

        return success_count

    def download_playlist(self, playlist_id, output_dir: Union[str, Path], metadata: bool = True, lyric: bool = True, num: int = 9999) -> int:
        song_ids = []
        cur_p = 1
        while len(song_ids) < num:
            playlist_info = self.s.get_album_info(playlist_id, pn=cur_p)
            if not playlist_info or not playlist_info.get("musicList"):
                break
            song_ids.extend(e.get("rid") for e in playlist_info.get("musicList"))

        success_count = 0
        for id_ in tqdm(song_ids[:num], "Playlist:{}".format(playlist_id)):
            if self.download_song(id_, output_dir, metadata, lyric):
                success_count += 1

        return success_count


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output_dir", default="kw_output", help="Where to save songs, default to 'kw_output/'")
    parser.add_argument("--metadata", action="store_true", default=True, help="Whether save tag info to songs, default to True")
    parser.add_argument("--lyric", action="store_true", default=True, help="Whether save lyric file, default to True")
    parser.add_argument("--num", type=int, default=100, help="Only used in artist, album or playlist, for download num for each one, default to 100")

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
            downloader.download_song(id_, output_dir, args.metadata, args.lyric)
    elif args.artist:
        for id_ in args.artist:
            downloader.download_artist(id_, output_dir, args.metadata, args.lyric, args.num)
    elif args.album:
        for id_ in args.album:
            downloader.download_album(id_, output_dir, args.metadata, args.lyric, args.num)
    elif args.playlist:
        for id_ in args.playlist:
            downloader.download_playlist(id_, output_dir, args.metadata, args.lyric, args.num)
    else:
        raise ArgumentError("No arguments specified.")
