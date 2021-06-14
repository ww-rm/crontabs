# -*- coding: UTF-8 -*-

from base64 import b64encode, b64decode
from pathlib import Path

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad


def aes256_encrypt(plain: str, key: str) -> str:
    key = key.encode("utf8")
    if len(key) != 32:
        raise ValueError("Incorrect key length, must be 256 bit.")

    encrypter = AES.new(key, AES.MODE_ECB)

    plain = pad(plain.encode("utf8"), 32, "pkcs7")
    cipher = encrypter.encrypt(plain)

    cipher = b64encode(cipher).decode("utf8")
    return cipher


def aes256_decrypt(cipher: str, key: str) -> str:
    key = key.encode("utf8")
    if len(key) != 32:
        raise ValueError("Incorrect key length, must be 256 bit.")
    decrypter = AES.new(key, AES.MODE_ECB)

    cipher = b64decode(cipher.encode("utf8"))

    plain = decrypter.decrypt(cipher)
    plain = unpad(plain, 32, "pkcs7").decode("utf8")
    return plain


def gen_rsa4096(export_dir):
    """Generate RSA 4096 private and public key pair

    export file names:
        private: rsa4096.pri.pem
        public: rsa4096.pub.pem

        the content is in base64 format
    """
    key = RSA.generate(4096)
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    # private key
    export_dir.joinpath(
        "rsa4096.pri.pem"
    ).write_bytes(
        b64encode(key.export_key(format="PEM"))
    )

    # public key
    export_dir.joinpath(
        "rsa4096.pub.pem"
    ).write_bytes(
        b64encode(key.publickey().export_key(format="PEM"))
    )


def rsa_encrypt(plain: str, public_key: str) -> str:
    """RSA with PKCS1_OAEP

    Args:
        plain: utf8 encoded plain string
        public_key: PEM, DER, OPENSSH format key string

    Returns:
        base64 encoded cipher string
    """
    key = RSA.import_key(public_key)
    encrypter = PKCS1_OAEP.new(key)

    cipher = encrypter.encrypt(plain.encode("utf8"))
    cipher = b64encode(cipher).decode("utf8")
    return cipher


def rsa_decrypt(cipher: str, private_key: str) -> str:
    """RSA with PKCS1_OAEP
    
    Args:
        cipher: base64 encoded cipher string
        public_key: PEM, DER, OPENSSH format key string

    Returns:
        utf8 encoded plain string
    """
    key = RSA.import_key(private_key)
    decrypter = PKCS1_OAEP.new(key)

    cipher = b64decode(cipher.encode("utf8"))
    plain = decrypter.decrypt(cipher).decode("utf8")
    return plain
