# -*- coding: UTF-8 -*-

import hashlib
from argparse import ArgumentParser
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Callable, Tuple

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad


def aes256_enc_cbc(plain: str, key: str) -> str:
    """AES256 in CBC mode and pkcs7 padding.

    Use sha256 to expand key, use fixed IV "0102030405060708".
    All strings will en(de)code in utf-8.

    Args:
        plain: plain to encrypt.
        key: key

    Returns:
        cipher (str): cipher in base64
    """
    key = key.encode("utf8")
    key = hashlib.sha256(key).digest()[:32]
    cbc_iv = b"0102030405060708"

    encrypter = AES.new(key, AES.MODE_CBC, cbc_iv)

    plain = pad(plain.encode("utf8"), 32, "pkcs7")
    cipher = encrypter.encrypt(plain)
    cipher = b64encode(cipher).decode("utf8")

    return cipher


def aes256_dec_cbc(cipher: str, key: str) -> str:
    """AES256 in CBC mode and pkcs7 padding.

    Use sha256 to expand key, use fixed IV "0102030405060708".
    All strings will en(de)code in utf-8.

    Args:
        cipher: cipher to decrypt.
        key: key

    Returns:
        plain (str): plain in base64
    """
    key = key.encode("utf8")
    key = hashlib.sha256(key).digest()[:32]
    cbc_iv = b"0102030405060708"

    decrypter = AES.new(key, AES.MODE_CBC, cbc_iv)

    cipher = b64decode(cipher.encode("utf8"))
    plain = decrypter.decrypt(cipher)
    plain = unpad(plain, 32, "pkcs7").decode("utf8")

    return plain


def gen_rsa4096(export_dir: Path, passphrase: str):
    """Generate RSA 4096 private and public key pair

    export file names:
        private: rsa4096.pri.pem, will be encrypted by passphrase.
        public: rsa4096.pub.pem

    Args:
        export_dir: dir to store key pair.
        passphrase: passphrase used for private key

    """
    key = RSA.generate(4096)
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    # private key
    export_dir.joinpath(
        "rsa4096.pri.pem"
    ).write_bytes(
        key.export_key(
            format="PEM",
            passphrase=passphrase,
            pkcs=8,
            protection="PBKDF2WithHMAC-SHA1AndAES256-CBC"
        )
    )

    # public key
    export_dir.joinpath(
        "rsa4096.pub.pem"
    ).write_bytes(
        key.publickey().export_key(format="PEM")
    )


def rsa_encrypt(plain: str, public_key: bytes) -> str:
    """RSA with PKCS1_OAEP

    Args:
        plain: utf8 encoded plain string
        public_key: PEM, DER, OPENSSH format key bytes

    Returns:
        base64 encoded cipher string
    """
    key = RSA.import_key(public_key)
    encrypter = PKCS1_OAEP.new(key)

    cipher = encrypter.encrypt(plain.encode("utf8"))
    cipher = b64encode(cipher).decode("utf8")
    return cipher


def rsa_decrypt(cipher: str, private_key: bytes, passphrase: str) -> str:
    """RSA with PKCS1_OAEP

    Args:
        cipher: base64 encoded cipher string
        private_key: PEM, DER, OPENSSH format key bytes
        passphrase: passphrase for private key

    Returns:
        utf8 encoded plain string
    """
    key = RSA.import_key(private_key, passphrase)
    decrypter = PKCS1_OAEP.new(key)

    cipher = b64decode(cipher.encode("utf8"))
    plain = decrypter.decrypt(cipher).decode("utf8")
    return plain


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    # group.add_argument("-g", dest="gen_dir", nargs=2, help="generate key pair: [export dir], [passphrase]")
    group.add_argument("-e", dest="encrypt", nargs=2, help="encryption: [key], [plain]")
    group.add_argument("-d", dest="decrypt", nargs=2, help="decryption: [key], [cipher]")

    args = parser.parse_args()
    # if args.gen_dir:
    #     gen_rsa4096(args.gen_dir[0], args.gen_dir[1])
    # else:
    if args.encrypt:
        key, plain = args.encrypt
        result = aes256_enc_cbc(plain, key)
    elif args.decrypt:
        key, cipher = args.decrypt
        result = aes256_dec_cbc(cipher, key)
    print(result)
