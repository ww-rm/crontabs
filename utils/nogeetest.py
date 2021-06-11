import json
import re
import secrets
from base64 import b64decode, b64encode

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

from .xsession import XSession

__version__ = "fullpage.9.0.5"


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

    def __init__(self, log_path) -> None:
        super().__init__(log_path)
        self.type = {}

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
        cipher = cls._aes_encrypt(plain.encode("utf8"), aes_key)
        cipher = cls._b64encrypt(cipher).decode("utf8")
        return cipher

    @classmethod
    def decrypt_msg(cls, cipher: str, aes_key: str) -> str:
        plain = cls._b64decrypt(cipher.encode("utf8"))
        plain = cls._aes_decrypt(plain, aes_key).decode("utf8")
        return plain

    def gettype(self, gt, callback="geetest_1666666666666") -> bool:
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

        self.type = json_.get("data")
        return True

    # def
