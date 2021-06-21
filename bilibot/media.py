from math import ceil, floor
from pathlib import Path
from typing import List, Union

import cv2
import moviepy.editor as mvp
import numpy as np


def load_images(img_paths: List[Union[str, Path]], load_size: tuple = (1080, 1920), padding_mode: str = "full_blurred") -> List[np.ndarray]:
    """Load local images to specified size and COLOR mode

    Args

    img_paths:
        A list of image paths to load
    load_size:
        A size tuple (height, width) image should resize to, will keep radio
    padding_mode:
        Can be "black", "full", "full_blurred", 
    """
    def _resize1(img: np.ndarray) -> np.ndarray:
        """adapt"""
        h, w = img.shape[0], img.shape[1]
        if h/w > load_size[0]/load_size[1]:
            # same height
            h, w = int(load_size[0]), int(load_size[0]*(w/h))
            return cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)
        else:
            # same width
            h, w = int(load_size[0]*(h/w)), int(load_size[0])
            return cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

    def _resize2(img: np.ndarray) -> np.ndarray:
        """pad"""
        h, w = img.shape[0], img.shape[1]
        if h/w > load_size[0]/load_size[1]:
            # same width
            h, w = int(load_size[1]*(h/w)), int(load_size[1])
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)
        else:
            # same height
            h, w = int(load_size[1]), int(load_size[1]*(w/h))
            img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)
        # crop
        delta_h, delta_w = img.shape[0] - load_size[0], img.shape[1] - load_size[1]
        if delta_h > 0:
            img = img[0:load_size[0]]
        if delta_w > 0:
            img = img[floor(delta_w/2):-ceil(delta_w/2)]
        return img

    def _pad_black(img: np.ndarray) -> np.ndarray:
        delta_h, delta_w = load_size[0] - img.shape[0], load_size[1] - img.shape[1]
        return cv2.copyMakeBorder(
            img,
            floor(delta_h/2), ceil(delta_h/2),
            floor(delta_w/2), ceil(delta_w/2),
            cv2.BORDER_CONSTANT, value=0
        )

    def _pad_full(img: np.ndarray) -> np.ndarray:
        h, w = img.shape[0], img.shape[1]
        delta_h, delta_w = load_size[0] - img.shape[0], load_size[1] - img.shape[1]
        fg = cv2.copyMakeBorder(
            img,
            floor(delta_h / 2), ceil(delta_h / 2),
            floor(delta_w / 2), ceil(delta_w / 2),
            cv2.BORDER_CONSTANT, value=0
        )
        bg = _resize2(img)
        _, mask = cv2.threshold(fg, 0, 255, cv2.THRESH_BINARY_INV)
        return cv2.bitwise_or(fg, cv2.bitwise_and(bg, mask))

    def _pad_full_blurred(img: np.ndarray) -> np.ndarray:
        h, w = img.shape[0], img.shape[1]
        delta_h, delta_w = load_size[0] - img.shape[0], load_size[1] - img.shape[1]
        fg = cv2.copyMakeBorder(
            img,
            floor(delta_h / 2), ceil(delta_h / 2),
            floor(delta_w / 2), ceil(delta_w / 2),
            cv2.BORDER_CONSTANT, value=0
        )
        bg = cv2.blur(_resize2(img), (20, 20))
        _, mask = cv2.threshold(fg, 0, 255, cv2.THRESH_BINARY_INV)
        return cv2.bitwise_or(fg, cv2.bitwise_and(bg, mask))

    images = []
    for path in map(Path, img_paths):
        img = cv2.imread(path.as_posix(), cv2.IMREAD_COLOR)
        img = _resize1(img)
        if padding_mode == "black":
            img = _pad_black(img)
        elif padding_mode == "full":
            img = _pad_full(img)
        elif padding_mode == "full_blurred":
            img = _pad_full_blurred(img)
        else:
            raise ValueError("Incorrect padding mode: '{}'".format(padding_mode))
        images.append(img)

    return images

def make_video(images: List[np.ndarray]):
    return