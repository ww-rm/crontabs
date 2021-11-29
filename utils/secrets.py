# -*- coding: UTF-8 -*-

from argparse import ArgumentParser
from base64 import b64decode, b64encode
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
        private_key: PEM, DER, OPENSSH format key string

    Returns:
        utf8 encoded plain string
    """
    key = RSA.import_key(private_key)
    decrypter = PKCS1_OAEP.new(key)

    cipher = b64decode(cipher.encode("utf8"))
    plain = decrypter.decrypt(cipher).decode("utf8")
    return plain


if __name__ == "__main__":

    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", dest="gen_dir", help="generate key pair: [export dir]")
    group.add_argument("-e", dest="encrypt", nargs=2, help="encryption: [content], [public_key]")
    group.add_argument("-d", dest="decrypt", nargs=2, help="decryption: [content], [private_key]")

    args = parser.parse_args()
    if args.gen_dir:
        gen_rsa4096(args.gen_dir)
    else:
        if args.encrypt:
            content = args.encrypt[0]
            key = args.encrypt[1]
            key = b64decode(key).decode("utf8")
            result = rsa_encrypt(content, key)
        elif args.decrypt:
            content = args.decrypt[0]
            key = args.decrypt[1]
            key = b64decode(key).decode("utf8")
            result = rsa_decrypt(content, key)
        print(result)
