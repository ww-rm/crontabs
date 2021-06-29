from .base import XSession, empty_retry


class KuwoMusic(XSession):
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

    def __init__(self, interval: float = 0.1) -> None:
        super().__init__(interval=interval)
        self.get(self.url_host)  # get csrf token for the first time

    def _get_csrf(self):
        if "kw_token" not in self.cookies:
            self.get(self.url_host)
        return self.cookies.get("kw_token", "")

    @empty_retry()
    def get_song_data(self, song_id, br: str = "320kmp3",
                      format_="mp3", response="url", type_="convert_url3", from_="web", httpsstatus=1) -> bytes:
        """
        Get the static resource data for a song

        Args

        song_id: 
            id of song
        br: 
            bit rate, can be "128kmp3", "192kmp3", "320kmp3"

        Note

        If can't find resource, will auto reduce bit rate and log warning info
        """
        bit_rate = ["320kmp3", "192kmp3", "128kmp3"]
        try:
            br_index = bit_rate.index(br)
        except ValueError:
            self.logger.warning("Incorrect 'br' value, default to use '320kmps'")
            br_index = 0

        for i in range(br_index, 3):
            res = self.get(
                self.song_url,
                params={
                    "rid": song_id,
                    "br": bit_rate[i],
                    "format_": format_,
                    "response": response,
                    "type": type_,
                    "from": from_,
                    "httpsStatus": httpsstatus,
                    # "t": 1624631124032,
                    # "reqId": "xxxx"
                }
            )
            # print(res.text)
            if res.status_code != 200:
                return b""
            try:
                if res.json().get("code") != 200:
                    return b""
                song_url = res.json().get("url", "")
            except ValueError:
                song_url = ""
                if i < 2:
                    self.logger.warning("KuwoMusic:Failed to get song:{} in bit rate:{}, try to get lower bit rate:{}".format(song_id, bit_rate[i], bit_rate[i+1]))
                else:
                    self.logger.error("KuwoMusic:Failed to get song data:{} in any bit rate.".format(song_id))
            else:
                break

        # get song data
        if not song_url:
            return b""

        res = self.get(song_url)
        if res.status_code != 200:
            return b""
        return res.content

    def get_music_info(self, song_id, httpsstatus=1) -> dict:
        res = self.get(
            self.api_www_music_musicinfo,
            params={
                "mid": song_id,
                "httpsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_playlist_info(self, playlist_id, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
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
            self.api_www_playlist_playlistinfo,
            params={
                "pid": playlist_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_album_info(self, album_id, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get music list of an album

        Args

        album_id:
            album_id
        pn:
            page num
        rn:
            return num in each page

        Returns

        If no music found, the field `musicList` in data will be empty list
        """
        res = self.get(
            self.api_www_album_albuminfo,
            params={
                "albumId": album_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_artist(self, artist_id, httpsstatus=1) -> dict:
        """Get info of an artist"""
        res = self.get(
            self.api_www_artist_artist,
            params={
                "artistid": artist_id,
                "httpsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_artist_music(self, artist_id, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get music list of an artist

        Args

        artist_id:
            artist_id
        pn:
            page num
        rn:
            return num in each page

        Returns

        If no music found, the field `list` in data will be empty list
        """
        res = self.get(
            self.api_www_artist_artistmusic,
            params={
                "artistid": artist_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_artist_album(self, artist_id, pn: int = 1, rn: int = 30, httpsstatus=1) -> dict:
        """Get album list of an artist

        Args

        artist_id:
            artist_id
        pn:
            page num
        rn:
            return num in each page

        Returns

        If no music found, the field `albumList` in data will be empty list
        """
        res = self.get(
            self.api_www_artist_artistalbum,
            params={
                "artistid": artist_id,
                "pn": max(pn, 1), "rn": max(rn, 1),
                "httsStatus": httpsstatus,
                # "reqId": ""
            },
            headers={"csrf": self._get_csrf()}
        )
        if res.status_code != 200 or res.json().get("code") != 200:
            return {}
        return res.json().get("data")

    def get_songinfo_and_lyric(self, song_id, httpsstatus=1) -> dict:
        """Get song info and lyric(mainly)"""

        res = self.get(
            self.singles_songinfo_and_lrc,
            params={"musicId": song_id, "httpsStatus": httpsstatus}
        )
        if res.status_code != 200 or res.json().get("status") != 200:
            return {}
        return res.json().get("data")
