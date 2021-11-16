from os import PathLike
from pathlib import Path
from typing import Iterator
import requests
from .base import XSession, empty_retry


class KuwoMusicBase(XSession):
    url_host = "http://www.kuwo.cn/"

    song_url = "http://www.kuwo.cn/url"

    play_detail = "http://www.kuwo.cn/play_detail/{song_id}"  # TODO
    singer_detail = "http://www.kuwo.cn/singer_detail/{singer_id}"  # TODO
    playlist_detail = "http://www.kuwo.cn/playlist_detail/{playlist_id}"  # TODO
    album_detail = "http://www.kuwo.cn/album_detail/{album_id}"  # TODO

    api_www_music_musicinfo = "http://www.kuwo.cn/api/www/music/musicInfo"
    api_www_artist_artistmusic = "http://www.kuwo.cn/api/www/artist/artistMusic"
    api_www_artist_artistalbum = "http://www.kuwo.cn/api/www/artist/artistAlbum"

    api_www_artist_artist = "http://www.kuwo.cn/api/www/artist/artist"
    api_www_playlist_playlistinfo = "http://www.kuwo.cn/api/www/playlist/playListInfo"
    api_www_album_albuminfo = "http://www.kuwo.cn/api/www/album/albumInfo"

    singles_songinfo_and_lrc = "http://m.kuwo.cn/newh5/singles/songinfoandlrc"

    def __init__(self, interval: float = 0.01) -> None:
        super().__init__(interval=interval)
        self.get(KuwoMusicBase.url_host)  # get csrf token for the first time

    def _get_csrf(self):
        if "kw_token" not in self.cookies:
            self.get(KuwoMusicBase.url_host)
        return self.cookies.get("kw_token", "")

    def _check_response(self, res: requests.Response) -> dict:
        """Check the status code and error code of a json response, and return main data.

        Args:
            res (Response): response to check

        Returns:
            data (json): empty dict or data dict, if empty, will log error info    
        """

        if res.status_code is None:
            return {}

        # status code of responses correctly returned must be 200
        # but "code" field in json data may not be 0
        if res.status_code != 200:
            return {}

        # check valid json data
        try:
            json_ = res.json()
        except ValueError:
            self.logger.error("{}:JsonValueError.".format(res.url))
            return {}

        # check error mesage
        if json_["code"] != 200:
            self.logger.error("{}:{}:{}".format(res.url, json_["code"], json_.get("message", "No msg.")))
            return {}
        return json_["data"]

    # BUG: song_url is deprecated.
    def _get_song_url(
        self,
        song_id: str,
        br: str = "320kmp3",
        format_="mp3", response="url",
        type_="convert_url3", from_="web", httpsstatus=1
    ) -> dict:
        """
        Get the url for a song.

        Args:
            song_id: id of song
            br: bit rate, can be "128kmp3", "192kmp3", "320kmp3"

        """
        res = self.get(
            KuwoMusicBase.song_url,
            params={
                "rid": song_id,
                "br": br,
                "format": format_,
                "response": response,
                "type": type_,
                "from": from_,
                "httpsStatus": httpsstatus,
                # "t": 1624631124032,
                # "reqId": "xxxx"
            }
        )

        return self._check_response(res)

    @empty_retry()
    def _get_song_data(self, song_url: str, chunk_size: int = 10485760) -> Iterator[bytes]:
        """"""
        res = self.get(song_url, stream=True)

        if res.status_code != 200:
            return b""
        return res.iter_content(chunk_size)

    def _get_music_info(self, song_id: str, httpsstatus=1) -> dict:
        res = self.get(
            KuwoMusicBase.api_www_music_musicinfo,
            params={
                "mid": song_id,
                "httpsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_playlist_info(self, playlist_id: str, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get info of a playlist

        Args

        playlist_id:
            plalist_id
        pn:
            page num
        rn:
            return num in each page

        Returns

        If no music found, the field `musicList` in data will be empty list
        """
        res = self.get(
            KuwoMusicBase.api_www_playlist_playlistinfo,
            params={
                "pid": playlist_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_album_info(self, album_id: str, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get music list of an album

        Args:
            album_id: album_id
            pn: page num
            rn: return num in each page

        Returns:
            If no music found, the field `musicList` in data will be empty list
        """
        res = self.get(
            KuwoMusicBase.api_www_album_albuminfo,
            params={
                "albumId": album_id,
                "pn": max(pn, 1),
                "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_artist(self, artist_id: str, httpsstatus=1) -> dict:
        """Get info of an artist."""
        res = self.get(
            KuwoMusicBase.api_www_artist_artist,
            params={
                "artistid": artist_id,
                "httpsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_artist_music(self, artist_id: str, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get music list of an artist.

        Args:
            artist_id: artist_id
            pn: page num
            rn: return num in each page

        Returns:
            If no music found, the field `list` in data will be empty list
        """
        res = self.get(
            KuwoMusicBase.api_www_artist_artistmusic,
            params={
                "artistid": artist_id,
                "pn": max(pn, 1),
                "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_artist_album(self, artist_id: str, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get album list of an artist

        Args:
            artist_id: artist_id
            pn: page num
            rn: return num in each page

        Returns:
            If no music found, the field `albumList` in data will be empty list.
        """
        res = self.get(
            KuwoMusicBase.api_www_artist_artistalbum,
            params={
                "artistid": artist_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        return self._check_response(res)

    def _get_songinfo_and_lyric(self, song_id: str, httpsstatus=1) -> dict:
        """Get song info and lyric. (mainly used for lyric.)"""

        res = self.get(
            KuwoMusicBase.singles_songinfo_and_lrc,
            params={
                "musicId": song_id,
                "httpsStatus": httpsstatus
            }
        )
        return self._check_response(res)


class KuwoMusic(KuwoMusicBase):
    """"""

    def download_song(self, song_id: str, save_path: PathLike, bit_rate: str = "320kmps") -> bool:
        # XXX: add cover and lyric
        # BUG: song url is deprected.
        """
        Note:
            If can't find resource, will auto reduce bit rate and log warning info.
        """

        br_list = ["320kmp3", "192kmp3", "128kmp3"]
        try:
            br_index = br_list.index(bit_rate)
        except ValueError:
            self.logger.warning("Incorrect 'bit_rate' value {}, default to use '320kmps'.".format(bit_rate))
            br_index = 0

        for i in range(br_index, 3):
            url_info = self._get_song_url(
                song_id, br_list[br_index]
            )
            if not url_info:
                self.logger.warning("KuwoMusic:Failed to get song url {} in bit rate:{}, try to get lower bit rate:{}".format(song_id, br_list[i], br_list[i+1]))
            else:
                break

        if not url_info:
            self.logger.error("KuwoMusic:Failed to get song url {}.".format(song_id))
            return False

        song_data = self._get_song_data(url_info["url"])
        if not song_data:
            self.logger.error("Failed to get song data {}.".format(song_id))
            return False

        with Path(save_path).open("wb") as f:
            for chunk in song_data:
                f.write(chunk)

        return True
