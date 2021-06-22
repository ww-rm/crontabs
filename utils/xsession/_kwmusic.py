import json
import os
from time import sleep

import requests
from bs4 import BeautifulSoup
from .base import XSession

# TODO
class KuwoMusic(XSession):
    """
    获取kuwo上的单首歌曲

    使用示例:
        kwsong = KwSong(99999999) # 创建对象
        kwsong.get_info() # 获取歌曲信息和歌词
        kwsong.get_lyric()
        kwsong.save_song() # 保存本地
        kwsong.save_lyric() # 保存歌词

    其中前两步是必须操作
    """

    url_detail = 'http://www.kuwo.cn/play_detail/{song_id}'
    url_resource = 'http://www.kuwo.cn/url'
    url_song_info = 'http://www.kuwo.cn/api/www/music/musicInfo'
    url_infoandlrc = 'http://m.kuwo.cn/newh5/singles/songinfoandlrc'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36 Edg/81.0.416.68',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'csrf': None
    }

    def __init__(self, song_id):
        self.url_detail = self.url_detail.format(song_id=song_id)
        self.song_id = song_id
        self.info = {}
        self.lyric = {}
        self.session = requests.Session()

        # 建立首次连接得到第一次的token
        self.session.headers = self.headers
        self.session.get(self.url_detail)

    def _valid_filename(self, filename):
        filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
        filename = filename.replace('*', '_').replace('?', '_').replace('"', '_')
        filename = filename.replace('<', '_').replace('>', '_').replace('|', '_')
        filename = filename.replace('\n', '').strip(' ')
        return filename

    def get_raw_data(self, chunk_size=1024):
        """
        获取歌曲源数据

        返回:
            成功返回指定大小的字节迭代器,
            失败返回None
        """

        # 请求源文件url
        self.session.headers['csrf'] = self.session.cookies.get('kw_token')
        response = self.session.get(
            self.url_resource,
            params={
                'type': 'convert_url3',
                'br': '320kmp3',
                'format': 'mp3',
                'response': 'url',
                'from': 'web',
                'rid': self.song_id
            }
        )

        # 判断请求是否成功
        result = response.json()
        if result.get('code') != 200:
            # print('okkk')
            return None

        # 请求源文件数据
        self.session.headers['csrf'] = self.session.cookies.get('kw_token')
        response = self.session.get(
            result.get('url', ''),
            stream=True
        )

        # 判断请求是否成功
        if response.status_code != 200:
            return None

        return response.iter_content(chunk_size)

    def get_info(self):
        """
        获取歌曲信息与歌词信息, 保存在属性里

        返回:
            返回一个bool二元组(info, lrc)
            代表对应的获取是否成功
        """

        # 请求歌曲信息
        self.session.headers['csrf'] = self.session.cookies.get('kw_token')
        response = self.session.get(
            self.url_song_info,
            params={
                'mid': self.song_id
            }
        )

        # 判断请求是否成功
        result = response.json()
        if result.get('code') != 200:
            return False

        # 将歌曲信息存入属性中
        self.info = result.get('data', {})
        self.info = {} if self.info is None else self.info

        return True

    def get_lyric(self):
        # 请求歌词信息
        self.session.headers['csrf'] = self.session.cookies.get('kw_token')
        response = self.session.get(
            self.url_infoandlrc,
            params={
                'musicId': self.song_id
            }
        )

        # 判断请求是否成功
        result = response.json()
        if result.get('status') != 200:
            return False

        self.lyric = result.get('data', {}).get('lrclist', {})
        self.lyric = {} if self.lyric is None else self.lyric

        return True

    def save_song(self, path='.'):
        """
        保存歌曲到本地, 文件名是[<songname> - <artist>.mp3]

        返回:
            返回bool值表示是否成功
        """

        # 获得源文件数据
        raw_data = self.get_raw_data()
        if raw_data is None:
            return False

        # 生成文件名
        filename = self.info.get('name', '')+' - '+self.info.get('artist', '')+'.mp3'
        filename = self._valid_filename(filename)

        # 保存本地文件
        filepath = path+'/'+filename
        with open(filepath, 'wb') as f:
            for chunk in raw_data:
                if chunk:
                    f.write(chunk)

        # 添加歌曲信息
        # XXX: 增加封面信息
        song_eyed3 = eyed3.load(filepath, eyed3.id3.ID3_V2)
        song_eyed3.initTag(eyed3.id3.ID3_V2_4)
        song_tag = song_eyed3.tag

        song_tag.title = self.info.get('name', '')
        song_tag.artist = self.info.get('artist', '')
        song_tag.album = self.info.get('album', '')

        song_tag.save()

        return True

    def save_lyric(self, path='.'):
        """
        保存歌词文件到本地

        返回:
            返回bool表示是否成功
        """

        # 生成文件名
        filename = self.info.get('name', '')+' - '+self.info.get('artist', '')+'.lrc'
        filename = self._valid_filename(filename)

        # 保存本地文件
        filepath = path+'/'+filename
        with open(filepath, 'w', encoding='utf8') as f:
            for lyricline in self.lyric:
                f.write('[')
                # 这里处理一下时间变成[min:sec.ms]的格式
                lyric_time = ['']
                lyric_time.extend(lyricline.get('time', '').split('.'))
                lyric_time[0] = str(int(lyric_time[1])//60)
                lyric_time[1] = str(int(lyric_time[1]) % 60)
                f.write(lyric_time[0])
                f.write(':')
                f.write(lyric_time[1])
                f.write('.')
                f.write(lyric_time[2])
                f.write(']')
                # 歌词文本
                f.write(lyricline.get('lineLyric', ''))
                f.write('\n')

        return True


class KwMusicBase:
    host = 'http://www.kuwo.cn'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36 Edg/81.0.416.68',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'csrf': None
    }

    def __init__(self):
        self.songlist = []

        # 建立连接
        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.get(self.host)

    def _request_get(self, url, params=None):
        # kw的get请求
        self.session.headers['csrf'] = self.session.cookies.get('kw_token')
        response = self.session.get(url, params=params)
        return response

    def get_songlist(self):
        raise NotImplementedError

    def save_songs(self, path, lyric):
        """
        将获取的该歌手的所有歌曲保存至本地, 耗时较长

        参数:
            path指定保存路径
            lyric指定是否同时保存歌词文件.lrc

        返回:
            {
                'total': xxx,
                'success': xxx,
                'fail': xxx
            }
        """

        # 留作多线程的时候向外传递下载情况
        self._dl_info = {
            'dl_total': len(self.songlist),
            'dl_current': 0,
            'dl_success': 0,
            'dl_fail': 0
        }

        # 最终要返回的信息
        saveinfo = {
            'total': len(self.songlist),
            'success': 0,
            'fail': 0
        }

        # 开始下载每一首歌
        print(f"total: {len(self.songlist)}")
        for song_id in self.songlist:
            self._dl_info['dl_current'] += 1

            song = KwSong(song_id)
            song.get_info()
            lrc_res = song.get_lyric()
            result = song.save_song(path)

            # 判断下载结果
            if result is True:
                self._dl_info['dl_success'] += 1
                saveinfo['success'] += 1
                print('success: {}'.format(song.info.get('name', '')))

                # 判断是否下载歌词
                if lyric is True and lrc_res is True:
                    song.save_lyric(path)
            else:
                self._dl_info['dl_fail'] += 1
                saveinfo['fail'] += 1
                print('fail: {}'.format(song.info.get('name', '')))

            # 防止访问过快
            sleep(0.1)

        return saveinfo


class KwArtist(KwMusicBase):
    url_detail = 'http://www.kuwo.cn/singer_detail/{artist_id}'
    url_artist_info = 'http://www.kuwo.cn/api/www/artist/artistMusic'

    def __init__(self, artist_id):
        super().__init__()
        self.url_detail = self.url_detail.format(artist_id=artist_id)
        self.artist_id = artist_id

        response = self.session.get(self.url_detail)
        self.artist_name = (
            BeautifulSoup(response.text, 'lxml')
            .find('span', attrs={'class': 'name'})
            .getText()
        )

    def get_songlist(self, page_num=1, savedata=False):
        """
        获取该歌手的歌曲的id, 耗时可能较长

        参数: 
            page_num指定下载第几面, 每一面为30首, 
            当page_num=0时,下载所有的歌曲, 可能会有1k+的情况

        返回:
            返回一个bool表示是否成功
            如果指定了savedata为True, 则同时将id列表保存至本地,
            文件名为[artist.<artist_id>]
        """

        # 请求信息和歌词
        # print('开始获取歌单信息...')
        response = self._request_get(
            self.url_artist_info,
            params={
                'artistid': self.artist_id,
                'pn': page_num if page_num != 0 else 1,
                'rn': 30 if page_num != 0 else 2000
            }
        )
        # print('请求已响应...')

        # 判断请求是否成功
        result = response.json()
        if result.get('code') != 200:
            return False
        # print(result)
        # 将歌所有歌曲的id提取出来
        for song_data in result.get('data', {}).get('list', {}):
            self.songlist.append(song_data.get('rid', ''))

        # 将所有歌曲的id保存至本地
        if savedata is True:
            with open('./artist.'+str(self.artist_id), 'w', encoding='utf8') as f:
                json.dump(self.songlist, f)

        return True

    def save_songs(self, path='.', lyric=True):
        """
        将获取的该歌手的所有歌曲保存至本地, 耗时较长

        参数:
            path指定保存路径
            lyric指定是否同时保存歌词文件.lrc

        返回:
            {
                'total': xxx,
                'success': xxx,
                'fail': xxx
            }
        """

        # 设置默认保存路径
        # XXX: 路径改成artist_<name>
        path = f'{path}/artist_{self.artist_id}_{self.artist_name}'
        os.makedirs(path, exist_ok=True)

        # 开始下载每一首歌
        saveinfo = super().save_songs(path, lyric)
        return saveinfo


class KwPlaylist(KwMusicBase):
    url_detail = 'http://www.kuwo.cn/playlist_detail/{playlist_id}'
    url_playlist_info = 'http://www.kuwo.cn/api/www/playlist/playListInfo'

    def __init__(self, playlist_id):
        super().__init__()
        self.url_detail = self.url_detail.format(playlist_id=playlist_id)
        self.playlist_id = playlist_id

    def get_songlist(self, savedata=False):
        """
        获取该歌单的所有歌曲的id, 耗时可能较长

        返回:
            返回一个bool表示是否成功
            如果指定了savedata为True, 则同时将id列表保存至本地,
            文件名为[playlist.<playlist_id>]
        """

        # 请求信息和歌词
        # print('开始获取歌单信息...')
        response = self._request_get(
            self.url_playlist_info,
            params={
                'pid': self.playlist_id,
                'pn': 1,
                'rn': 2000
            }
        )
        # print('请求已响应...')

        # 判断请求是否成功
        result = response.json()
        if result.get('code') != 200:
            return False

        # 将歌所有歌曲的id提取出来
        for song_data in result.get('data', {}).get('musicList', {}):
            self.songlist.append(song_data.get('rid', ''))

        # 将所有歌曲的id保存至本地
        if savedata is True:
            with open('./playlist.'+str(self.playlist_id), 'w', encoding='utf8') as f:
                json.dump(self.songlist, f)

        return True

    def save_songs(self, path='.', lyric=True):
        """
        将获取的该歌单的所有歌曲保存至本地, 耗时较长

        参数:
            path指定保存路径
            lyric指定是否同时保存歌词文件.lrc

        返回:
            {
                'total': xxx,
                'success': xxx,
                'fail': xxx
            }
        """

        # 设置默认保存路径
        path = path+'/playlist_'+str(self.playlist_id)
        os.makedirs(path, exist_ok=True)

        # 开始下载每一首歌
        saveinfo = super().save_songs(path, lyric)
        return saveinfo


class KwAlbum(KwMusicBase):
    url_detail = 'http://www.kuwo.cn/album_detail/{album_id}'
    url_album_info = 'http://www.kuwo.cn/api/www/album/albumInfo'

    def __init__(self, album_id):
        super().__init__()
        self.url_detail = self.url_detail.format(album_id=album_id)
        self.album_id = album_id

    def get_songlist(self, savedata=False):
        """
        获取该专辑的所有歌曲的id, 耗时可能较长

        返回:
            返回一个bool表示是否成功
            如果指定了savedata为True, 则同时将id列表保存至本地,
            文件名为[album.<album_id>]
        """

        # 请求信息和歌词
        # print('开始获取歌单信息...')
        response = self._request_get(
            self.url_album_info,
            params={
                'albumId': self.album_id,
                'pn': 1,
                'rn': 2000
            }
        )
        # print('请求已响应...')

        # 判断请求是否成功
        result = response.json()
        if result.get('code') != 200:
            return False

        # 将歌所有歌曲的id提取出来
        for song_data in result.get('data', {}).get('musicList', {}):
            self.songlist.append(song_data.get('rid', ''))

        # 将所有歌曲的id保存至本地
        if savedata is True:
            with open('./album.'+str(self.album_id), 'w', encoding='utf8') as f:
                json.dump(self.songlist, f)

        return True

    def save_songs(self, path='.', lyric=True):
        """
        将获取的该专辑的所有歌曲保存至本地, 耗时较长

        参数:
            path指定保存路径
            lyric指定是否同时保存歌词文件.lrc

        返回:
            {
                'total': xxx,
                'success': xxx,
                'fail': xxx
            }
        """

        # 设置默认保存路径
        path = path+'/album_'+str(self.album_id)
        os.makedirs(path, exist_ok=True)

        # 开始下载每一首歌
        saveinfo = super().save_songs(path, lyric)
        return saveinfo


def downloadSong(song_id, path='.'):
    """一键式下载歌曲"""

    kwsong = KwSong(song_id)
    kwsong.get_info()
    kwsong.get_lyric()
    kwsong.save_song(path)
    kwsong.save_lyric(path)


def downloadArtist(artist_id, page_num=1, path='.'):
    """一键式下载歌手"""

    kwartist = KwArtist(artist_id)
    kwartist.get_songlist(page_num)
    result = kwartist.save_songs(path)
    print(result)


def downloadPlaylist(playlist_id, path='.'):
    """一键式下载歌单"""

    kwplaylist = KwPlaylist(playlist_id)
    kwplaylist.get_songlist()
    result = kwplaylist.save_songs(path)
    print(result)


def downloadAlbum(album_id, path='.'):
    """一键式下载专辑"""

    kwalbum = KwAlbum(album_id)
    kwalbum.get_songlist()
    result = kwalbum.save_songs(path)
    print(result)


if __name__ == '__main__':
    pass
    # a = KwArtist(12033)
    # a.get_songlist()
    downloadSong(147040172, './Automusic/music')
    # downloadArtist(12033)
    # downloadPlaylist(3002579541)
    # downloadAlbum(11246770)
