import argparse
from os import PathLike
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


class MirageTank:

    @staticmethod
    def _mergeimg(cover, secret) -> np.ndarray:
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
    def _adjustimg(cover, secret) -> Tuple[np.ndarray, np.ndarray]:
        """adjust image to fit mergimg function"""
        # 图像需要是灰度图

        c_height, c_width = cover.shape
        s_height, s_width = secret.shape

        if (c_height / c_width) > (s_height / s_width):
            # same width
            cover = cv2.resize(
                cover,
                (s_width, int(c_height*s_width/c_width + 0.5)),
                interpolation=cv2.INTER_CUBIC
            )
        else:
            # same height
            cover = cv2.resize(
                cover,
                (int(c_width*s_height/c_height + 0.5), s_height),
                interpolation=cv2.INTER_CUBIC
            )

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
    def load_cover_and_secret(cover_path, secret_path) -> Tuple[np.ndarray, np.ndarray]:
        """load cover and secret in correct format"""
        return (
            cv2.imread(Path(cover_path).as_posix(), cv2.IMREAD_GRAYSCALE),
            cv2.imread(Path(secret_path).as_posix(), cv2.IMREAD_GRAYSCALE)
        )

    @staticmethod
    def save_mirage(mirage, save_path) -> Path:
        """save mirage in correct format"""
        save_path = Path(save_path).with_suffix(".png")
        cv2.imwrite(save_path.as_posix(), mirage)
        return save_path

    @staticmethod
    def make_mirage(cover_path, secret_path, save_path) -> Path:
        """make a mirage image with three paths"""
        cover, secret = MirageTank.load_cover_and_secret(cover_path, secret_path)
        if isinstance(cover, np.ndarray) and isinstance(secret, np.ndarray):
            mirage = MirageTank.makeimg(cover, secret)
            return MirageTank.save_mirage(mirage, save_path)
        else:
            return None

    

class BlackTank:
    @staticmethod
    def _adjustimg(img: np.ndarray) -> np.ndarray:
        img_black = np.zeros(img.shape, dtype=np.uint8)
        img_alpha = 255 - img

        img_out = np.stack([img_black, img_black, img_black, img_alpha], axis=2)
        return img_out

    @staticmethod
    def load_img(img_path: PathLike) -> np.ndarray:
        return cv2.imread(Path(img_path).as_posix(), cv2.IMREAD_GRAYSCALE)

    @staticmethod
    def save_img(img: np.ndarray, save_path: PathLike) -> Path:
        save_path = Path(save_path).with_suffix(".png")
        cv2.imwrite(save_path.as_posix(), img)
        return save_path

    @staticmethod
    def make_blacktank(img_path: PathLike, save_path: PathLike) -> Path:
        img = BlackTank.load_img(img_path)
        if isinstance(img, np.ndarray):
            img = BlackTank._adjustimg(img)
            return BlackTank.save_img(img, save_path)
        else:
            return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cover", type=str, help="cover(white) image")
    parser.add_argument("secret", type=str, help="secret(black) image")
    parser.add_argument("dest", type=str, help="dest path, if not \".png\" suffix, will replace to \".png\"")

    args = parser.parse_args()

    MirageTank.make_mirage(args.cover, args.secret, args.dest)
