import argparse
from pathlib import PurePath

import cv2
import numpy as np


class MirageTank:

    @staticmethod
    def _mergeimg(cover, secret):
        """merge cover over secret"""
        # 需要是灰度图
        # 转换图片数据类型为浮点数
        cover = cover.astype("float64")
        secret = secret.astype("float64")

        # 检查像素点 min(delta) >= 0, 调整图像
        c_min = np.min(cover)
        s_max = np.max(secret)

        # 二次函数调整, cover: [128, 255], secret: [0, 128]
        cover = cover + ((128-c_min)/(256-c_min)**2) * (256-cover)**2
        secret = secret - ((s_max-128) / s_max**2) * (secret**2)

        # 计算新图, 要求 min(delta) >= 0
        delta = cover - secret
        mirage_a = 255 - delta
        mirage_grey = 255 * secret / mirage_a

        mirage = np.stack([mirage_grey, mirage_grey, mirage_grey, mirage_a], axis=2).astype("uint8")
        return mirage

    @staticmethod
    def _adjustimg(cover, secret):
        """adjust image to fit mergimg function"""
        # 图像需要是灰度图

        s_height, s_width = secret.shape

        c_height, c_width = cover.shape

        if c_height < s_height:
            cover = cv2.resize(cover, (int(c_width*s_height/c_height + 0.5), s_height), interpolation=cv2.INTER_CUBIC)
            c_height, c_width = cover.shape

        if c_width < s_width:
            cover = cv2.resize(cover, (s_width, int(c_height*s_width/c_width + 0.5)), interpolation=cv2.INTER_CUBIC)
            c_height, c_width = cover.shape

        delta_height = c_height - s_height
        delta_width = c_width - s_width
        secret = cv2.copyMakeBorder(
            secret,
            delta_height//2, (delta_height+1)//2,
            delta_width//2, (delta_width+1)//2,
            cv2.BORDER_CONSTANT, value=0
        )

        return (cover, secret)

    @staticmethod
    def makeimg(cover, secret):
        """make mirage image"""
        cover, secret = MirageTank._adjustimg(cover, secret)
        return MirageTank._mergeimg(cover, secret)

    @staticmethod
    def load_cover_and_secret(cover_path, secret_path):
        """load cover and secret in correct format"""
        return (
            cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE),
            cv2.imread(secret_path, cv2.IMREAD_GRAYSCALE)
        )

    @staticmethod
    def save_mirage(mirage, save_path):
        """save mirage in correct format"""
        return cv2.imwrite(PurePath(save_path).with_suffix(".png").as_posix(), mirage)

    @staticmethod
    def make_mirage(cover_path, secret_path, save_path):
        """make a mirage image with three paths"""
        cover, secret = MirageTank.load_cover_and_secret(cover_path, secret_path)
        mirage = MirageTank.makeimg(cover, secret)
        MirageTank.save_mirage(mirage, save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cover", type=str, help="cover(white) image")
    parser.add_argument("secret", type=str, help="secret(black) image")
    parser.add_argument("dest", type=str, help="dest path, if not \".png\" suffix, will replace to \".png\"")

    args = parser.parse_args()

    MirageTank.make_mirage(args.cover, args.secret, args.dest)
