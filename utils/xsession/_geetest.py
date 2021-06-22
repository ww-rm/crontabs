# -*- coding: UTF-8 -*-

import json
import re
import secrets
from base64 import b64decode, b64encode

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

from .xsession import XSession

__version__ = "fullpage.9.0.5"


def get_validate(gt: str, challenge: str) -> str:
    raise NotImplementedError


def _bigintlist2int(bigintlist: list) -> int:
    # [lowest, ..., highest]
    # 28 bit for each num
    bigint = 0
    i = 0
    for int28bit in bigintlist:
        bigint += (int28bit << i)
        i += 28
    return bigint


class GeeSession(XSession):
    AES_IV: bytes = b"0000000000000000"
    RSA_E: int = 65537
    RSA_N: int = 136153462421446847404340432441046996374735571025589056967906613334049032306309642600950180794472974184474850029075084679952125029724775675860862428869529368335136951744118770626613042094193316007621445630035543273179259178158896311604233203144417656446177150555868699549873157540592293125574640692009097735041
    B64_ENCRYPT_TAB = [
        [2, 3, 4, 5, 0, 6, 7, 1],
        [0, 1, 4, 2, 5, 6, 3, 7],
        [0, 1, 6, 2, 7, 3, 4, 5],
    ]
    B64_DECRYPT_TAB = [
        [4, 7, 0, 1, 2, 3, 5, 6],
        [0, 1, 3, 6, 2, 4, 5, 7],
        [0, 1, 3, 5, 6, 7, 2, 4],
    ]

    url_gettype = "https://api.geetest.com/gettype.php"  # ?gt=7fa7d480550df273db851dcb2b04babf&callback=geetest_1623250398278"
    url_get = "https://api.geetest.com/get.php"  # ?gt=7fa7d480550df273db851dcb2b04babf&challenge=438b78e035cdb82521ffe8ca31739305&lang=zh-cn&pt=0&client_type=web&w="
    url_ajax = "https://api.geetest.com/ajax.php"  # ?gt=7fa7d480550df273db851dcb2b04babf&challenge=861cd237bcf4e505fa75970fe50a303f&lang=zh-cn&pt=0&client_type=web&w"

    def __init__(self, log_path) -> None:
        super().__init__(log_path)
        self.data = {}

    @classmethod
    def _mixbit(cls, _old: int, _mix_table: list) -> int:
        assert len(_mix_table) == 8
        _new = 0
        for _i, _j in enumerate(_mix_table):
            _new |= ((_old >> _i) & 1) << _j
        return _new

    @classmethod
    def _b64encrypt(cls, s: bytes) -> bytes:
        s = bytearray(s)
        for i, b in enumerate(s):
            s[i] = cls._mixbit(s[i], cls.B64_ENCRYPT_TAB[i % 3])
        s = b64encode(s, b"()").replace(b"=", b".")
        s = bytes(s)
        return s

    @classmethod
    def _b64decrypt(cls, s: bytes):
        s = b64decode(s.replace(b".", b"="), b"()")
        s = bytearray(s)
        for i, b in enumerate(s):
            s[i] = cls._mixbit(s[i], cls.B64_DECRYPT_TAB[i % 3])
        s = bytes(s)
        return s

    @classmethod
    def _aes_encrypt(cls, plain: bytes, key: bytes) -> bytes:
        encrypter = AES.new(key, AES.MODE_CBC, cls.AES_IV)

        plain = pad(plain, 16, "pkcs7")
        cipher = encrypter.encrypt(plain)
        return cipher

    @classmethod
    def _aes_decrypt(cls, cipher: bytes, key: bytes) -> bytes:
        decrypter = AES.new(key, AES.MODE_CBC, cls.AES_IV)

        plain = decrypter.decrypt(cipher)
        plain = unpad(plain, 16, "pkcs7")
        return plain

    @classmethod
    def _rsa_encrypt(cls, plain: bytes) -> str:
        key = RSA.construct((cls.RSA_N, cls.RSA_E))
        encrypter = PKCS1_v1_5.new(key)

        cipher = encrypter.encrypt(plain).hex()
        cipher = "0"+cipher if len(cipher) & 1 else cipher
        return cipher

    @classmethod
    def encrypt_msg(cls, plain: str, aes_key: str) -> str:
        cipher = cls._aes_encrypt(plain.encode("utf8"), aes_key.encode("utf8"))
        cipher = cls._b64encrypt(cipher).decode("utf8")
        return cipher

    @classmethod
    def decrypt_msg(cls, cipher: str, aes_key: str) -> str:
        plain = cls._b64decrypt(cipher.encode("utf8"))
        plain = cls._aes_decrypt(plain, aes_key.encode("utf8")).decode("utf8")
        return plain

    @classmethod
    def prepparam(cls, json_data: str) -> str:
        aes_key = "qwerghjkmnbvfdsa"
        encrypted_aes_key = cls._rsa_encrypt(aes_key.encode("utf8"))
        encrypted_data = cls.encrypt_msg(json_data, aes_key)
        param = encrypted_data + encrypted_aes_key
        return param

    def get_type(self, gt, callback="geetest_1666666666666") -> bool:
        """
        response body

        "callback(
                    {
                        "status": "success",
                        "data": {
                            "static_servers": ["static.geetest.com/", "dn-staticdown.qbox.me/"],
                            "aspect_radio": {"pencil": 128, "beeline": 50, "voice": 128, "click": 128, "slide": 103},
                            "fullpage": "/static/js/fullpage.9.0.5.js",
                            "voice": "/static/js/voice.1.2.0.js",
                            "click": "/static/js/click.3.0.0.js",
                            "slide": "/static/js/slide.7.8.1.js",
                            "pencil": "/static/js/pencil.1.0.3.js",
                            "beeline": "/static/js/beeline.1.0.1.js",
                            "geetest": "/static/js/geetest.6.0.9.js",
                            "type": "fullpage"
                        }
                    }
                )"
        """

        res = self.get(
            self.url_gettype,
            params={"gt": gt, "callback": callback}
        )
        if res.status_code != 200:
            return False
        else:
            json_, *_ = re.findall(callback+r"\((.*)\)", res.text)
            json_ = json.loads(json_)
            if json_.get("status") != "success":
                return False

        self.data.update(json_.get("data"))
        return True

    # get.php
    def get_info(self, gt, challenge, w, lang="zh-cn", pt=0, client_type="web", callback="geetest_1666666666666"):
        """
        param w: include aes_key

        {
            "area": "#geetest-wrap",
            "gt": "7fa7d480550df273db851dcb2b04babf",
            "challenge": "ec37987b05890691b04da4afdcf25c48",
            "new_captcha": True,
            "next_width": "270px",
            "product": "bind",
            "protocol": "https://",
            "cc": 8,
            "ww": True,
            "i": "102353!!309870!!CSS1Compat!!66!!-1!!-1!!-1!!-1!!3!!1!!-1!!-1!!6!!7!!2!!3!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!-1!!270!!43!!-1!!-1!!-1!!-7!!-7!!0!!0!!403!!577!!1295!!704!!zh-CN!!zh-CN,zh,zh-TW,zh-HK,en-US,en!!-1!!1.5!!24!!Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0!!1!!1!!1280!!720!!1280!!689!!1!!1!!1!!-1!!Win32!!1!!-8!!75fc76bf3f2653a191a9a5ed41ec80f6!!dea1a749065c7a277ca7ce929058525e!!!!0!!-1!!0!!8!!Arial,ArialBlack,Calibri,Cambria,CambriaMath,ComicSansMS,Consolas,Courier,CourierNew,Georgia,Helvetica,Impact,LucidaConsole,LucidaSansUnicode,MicrosoftSansSerif,MSGothic,MSPGothic,MSSansSerif,MSSerif,MYRIADPRO,PalatinoLinotype,SegoePrint,SegoeScript,SegoeUI,SegoeUILight,SegoeUISemibold,SegoeUISymbol,Tahoma,Times,TimesNewRoman,TrebuchetMS,Verdana,Wingdings!!1623398801661!!-1!!-1!!-1!!126!!18!!4!!226!!12!!-1!!-1"

            # gettype response body
            "static_servers": ["static.geetest.com/", "dn-staticdown.qbox.me/"],
            "aspect_radio": {"slide": 103, "pencil": 128, "voice": 128, "beeline": 50, "click": 128},
            "fullpage": "/static/js/fullpage.9.0.5.js",
            "slide": "/static/js/slide.7.8.1.js",
            "beeline": "/static/js/beeline.1.0.1.js",
            "click": "/static/js/click.3.0.0.js",
            "pencil": "/static/js/pencil.1.0.3.js",
            "voice": "/static/js/voice.1.2.0.js",
            "geetest": "/static/js/geetest.6.0.9.js",
            "type": "fullpage",
        }
        """

    # ajax.php
    def get_captcha_type(self, gt, challenge, w, lang="zh-cn", pt=0, client_type="web", callback="geetest_1666666666666"):
        """
        param w: no aes_key, (the same as last get_info request)

        {
            "lang": "zh-cn",
            "type": "fullpage",
            "tt": "M5ff38Pjp8Pjp8NN38Pc9UbA38-U*P)BMBBBBCBLiBBFggeJiJDABJg6BABBDiBBBBBBBBBg0JBA/BDfFDBDB9-TTc(?-)-9-:(?-)-9-:(?-)-M9d-?-9M:/)-1/:-1/:h*-:1:(:F)DN*)QHI9M:.g-1-:p)Q:*)-:*)-:*)Q:*)-:(:~-1/:-)4c-9-:*)-:*)Q:(?p)Q:(:RN-9-a-:(?-)-9-:3)Q1/:-1-:-)-9-VA:-).L6i9O-)-9-:(?-)-9-:(?-:(:M:(?.6-1-:-1-:-)19-C9:YPM_U9-N(:-13:MF)j.2?A-)-9MF-9-:(?-1/:1B7a2E*(U,(((,5bb(((n((5n,bne((((,n(b(((,,(((e8b,55oQZ1)D)NeF3B,F*/)MAMb-1/*5E7(G39M1)25-,bEBg9hRgb915-)b91EX),5-.1E1(MEAj?(4)(gRg9?5P-b4)MI-*b96(1E3(1d:gRh9c3*(?*)(?-c1?(U-(/,M)bE3.(1-*(N3)M9M9-NM9)qqM)qqiqqb(((99-jM*WWW((LM(/E()NM(()MEE(3UK(()TM/q()p(((FNj0j(()p(()SK75Kp6,c(8.MhDPbY4pl/9.(MI*)91/?-UQ/*(RMM2*(U9E5*(b56,bm-F1F95*(R)(*6MM:Z0j3-1W3Gp,s)E53F.R:hB(MW916(MN*9b1-NWNP(MA*(b1(1*XeDFC*,TMb:XN(C*)Y?E5.Mb5,(/n85@,2(MA*(b1(?3f@.:(Md91/A*(b1(((((7b(,qqM((8qn((((",
            "light": "LABEL_0|INPUT_1|INPUT_2|INPUT_3",
            "s": "c7c3e21112fe4f741921cb3e4ff9f7cb",
            "h": "bdf7469f3d83c1763c1e62bfd73681aa",
            "hh": "89c05a42063023ea6d7c3b0965ace2e7",
            "hi": "953ef7cee72400dc48e1882d37600073",
            "vip_order": -1,
            "ct": -1,
            "ep": {
                "v": "9.0.5",
                "de": False,
                "te": False,
                "me": True,
                "ven": "Google Inc.",
                "ren": "ANGLE (Intel(R) UHD \nGraphics 620 Direct3D11 vs_5_0 ps_5_0)",
                "fp": ["scroll", 985, 28, 1623398814440, None],
                "lp": ["up", 136, 469, 1623398822345, "pointerup"],
                "em": {"ph": 0, "cp": 0, "ek": "f1", "wd": 1, "nt": 0, "si": 0, "sc": 0},
                "tm": {
                    "a": 1623398800063,
                    "b": 1623398800338,
                    "c": 1623398800338,
                    "d": 0,
                    "e": 0,
                    "f": 1623398800064,
                    "g": 1623398800127,
                    "h": 1623398800219,
                    "i": 1623398800219,
                    "j": 1623398800270,
                    "k": 1623398800244,
                    "l": 1623398800270,
                    "m": 1623398800315,
                    "n": 1623398800315,
                    "o": 1623398800338,
                    "p": 1623398800677,
                    "q": 1623398800681,
                    "r": 1623398800687,
                    "s": 1623398801158,
                    "t": 1623398801158,
                    "u": 1623398801218
                },
                "by": 2
            },
            "passtime": 20798,
            "rp": "71e5d7f66f432e99bb2ef18decd27773",
            "captcha_token": "1300143123"
        }
        """

    # # # # # # # # # slide.js # # # # # # # # # # # # # #
    # 可以直接重放
    def get_captcha_info(
        self, gt, challenge, type_,
        lang="zh-cn", https=False, protocol="https://",
        product="embed", api_server="api.geetest.com", isPC=True, autoReset=True,
        area="#geetest-wrap", width="100%", callback="geetest_1666666666666"
    ):
        """
        response body:

        {
            "id": "aec37987b05890691b04da4afdcf25c48",
            "gt": "7fa7d480550df273db851dcb2b04babf",
            "challenge": "ec37987b05890691b04da4afdcf25c48g9",
            "static_servers": ["static.geetest.com/", "dn-staticdown.qbox.me/"],
            "slice": "pictures/gt/e06244a32/slice/da9c20988.png",
            "fullbg": "pictures/gt/e06244a32/e06244a32.jpg",
            "bg": "pictures/gt/e06244a32/bg/da9c20988.jpg",
            "width": "100%",
            "benchmark": False,
            "show_delay": 250,
            "i18n_labels": {
                "success": "sec 秒的速度超过 score% 的用户",
                "slide": "\u62d6\u52a8\u6ed1\u5757\u5b8c\u6210\u62fc\u56fe",
                "forbidden": "\u602a\u7269\u5403\u4e86\u62fc\u56fe\uff0c\u8bf7\u91cd\u8bd5",
                "voice": "\u89c6\u89c9\u969c\u788d",
                "cancel": "\u53d6\u6d88",
                "feedback": "\u5e2e\u52a9\u53cd\u9988",
                "close": "\u5173\u95ed\u9a8c\u8bc1",
                "logo": "\u7531\u6781\u9a8c\u63d0\u4f9b\u6280\u672f\u652f\u6301",
                "error": "\u8bf7\u91cd\u8bd5",
                "fail": "\u8bf7\u6b63\u786e\u62fc\u5408\u56fe\u50cf",
                "loading": "\u52a0\u8f7d\u4e2d...",
                "refresh": "\u5237\u65b0\u9a8c\u8bc1",
                "read_reversed": False,
                "tip": "\u8bf7\u5b8c\u6210\u4e0b\u65b9\u9a8c\u8bc1"
            },
            "link": "",
            "height": 160,
            "fullpage": True,
            "https": False,
            "so": 0,
            "xpos": 0,
            "mobile": True,
            "hide_delay": 800,
            "api_server": "http://api.geetest.com/",
            "s": "5f726757",
            "product": "embed",
            "gct_path": "/static/js/gct.41c7c9a25370d647813fc09db03b0af2.js",
            "type": "multilink",
            "feedback": "",
            "version": "6.0.9",
            "template": "",
            "theme": "ant",
            "c": [12, 58, 98, 36, 43, 95, 62, 15, 12],
            "ypos": 91,
            "clean": True,
            "logo": False,
            "theme_version": "1.2.6"
        }
        """
        # get.php

    def get_slide_validate(self, gt, challenge, w, lang="zh-cn", pt=0, client_type="web", callback="geetest_1666666666666"):
        """        
        param w: include aes_key

        {
            "lang": "zh-cn",
            "userresponse": "5252222255525225211a",
            "passtime": 626,
            "imgload": 147,
            "aa": "V/43323/--,Jk)(!!Ft((!)!,!*!,!*y(u(!)yztthts(!!(E:9::9::9::9:9:N::9$-G",
            "ep": {
                "v": "7.8.1",
                "te": False,
                "me": True,
                "tm": {
                    "a": 1623401956011,
                    "b": 1623401956319,
                    "c": 1623401956319,
                    "d": 0,
                    "e": 0,
                    "f": 1623401956015,
                    "g": 1623401956095,
                    "h": 1623401956183,
                    "i": 1623401956183,
                    "j": 1623401956255,
                    "k": 1623401956228,
                    "l": 1623401956255,
                    "m": 1623401956311,
                    "n": 1623401956311,
                    "o": 1623401956319,
                    "p": 1623401956740,
                    "q": 1623401956743,
                    "r": 1623401956747,
                    "s": 1623401957139,
                    "t": 1623401957139,
                    "u": 1623401957195
                },
                "td": -1
            },
            "eken": "1299891482",
            "rp": "4fc53644bf8ddb74c60862097d6dc166"
        }
        """
        # ajax.php
