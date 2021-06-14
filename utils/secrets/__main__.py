# -*- coding: UTF-8 -*-

from argparse import ArgumentParser
from base64 import b64decode

from .cryptoalg import gen_rsa4096, rsa_decrypt, rsa_encrypt

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
