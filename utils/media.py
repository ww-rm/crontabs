"""Do some media process."""

import hashlib
import secrets
from math import ceil, floor
from os import PathLike
from pathlib import Path
from typing import List, Tuple, Union

import cv2
import moviepy.editor as mvp
import numpy as np


def load_images(img_paths: List[Union[str, Path]], load_size: tuple = (1080, 1920), padding_mode: str = "full_blurred") -> List[np.ndarray]:
    """Load local images to specified size and `RGB` mode

    Args:
        img_paths: A list of image paths to load.
        load_size: A size tuple (height, width) image should resize to, will keep radio.
        padding_mode: Can be "black", "full", "full_darker", "full_blurred",
    """

    def _resize1(img: np.ndarray) -> np.ndarray:
        """adapt"""
        _h, _w = img.shape[0], img.shape[1]
        if _h/_w > load_size[0]/load_size[1]:
            # same height
            h, w = int(load_size[0]), int(load_size[0]*(_w/_h))
            return cv2.resize(img, (w, h), interpolation=(cv2.INTER_CUBIC if _w < w else cv2.INTER_LINEAR))
        else:
            # same width
            h, w = int(load_size[1]*(_h/_w)), int(load_size[1])
            return cv2.resize(img, (w, h), interpolation=(cv2.INTER_CUBIC if _h < h else cv2.INTER_LINEAR))

    def _resize2(img: np.ndarray) -> np.ndarray:
        """pad"""
        _h, _w = img.shape[0], img.shape[1]
        if _h/_w > load_size[0]/load_size[1]:
            # same width
            h, w = int(load_size[1]*(_h/_w)), int(load_size[1])
            img = cv2.resize(img, (w, h), interpolation=(cv2.INTER_CUBIC if _h < h else cv2.INTER_LINEAR))
        else:
            # same height
            h, w = int(load_size[0]), int(load_size[0]*(_w/_h))
            img = cv2.resize(img, (w, h), interpolation=(cv2.INTER_CUBIC if _w < w else cv2.INTER_LINEAR))
        # crop
        delta_h, delta_w = img.shape[0] - load_size[0], img.shape[1] - load_size[1]
        if delta_h > 0:
            img = img[0:load_size[0]]
        if delta_w > 0:
            img = img[:, floor(delta_w/2):-ceil(delta_w/2)]
        return img

    def _pad_black(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """(img, mask)"""
        delta_h, delta_w = load_size[0] - img.shape[0], load_size[1] - img.shape[1]
        img = cv2.copyMakeBorder(
            img,
            floor(delta_h/2), ceil(delta_h/2),
            floor(delta_w/2), ceil(delta_w/2),
            cv2.BORDER_CONSTANT, value=0
        )
        _, mask = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV)
        return (img, mask)

    def _pad_full(img: np.ndarray) -> np.ndarray:
        fg, mask = _pad_black(img)
        bg = _resize2(img)
        return cv2.bitwise_or(fg, cv2.bitwise_and(bg, mask))

    def _pad_full_darker(img: np.ndarray) -> np.ndarray:
        fg, mask = _pad_black(img)
        bg = cv2.addWeighted(_resize2(img), 0.5, 0, 0, 0)
        return cv2.bitwise_or(fg, cv2.bitwise_and(bg, mask))

    def _pad_full_blurred(img: np.ndarray) -> np.ndarray:
        fg, mask = _pad_black(img)
        bg = cv2.blur(_resize2(img), (20, 20))
        return cv2.bitwise_or(fg, cv2.bitwise_and(bg, mask))

    images = []
    for path in map(Path, img_paths):
        img = cv2.imread(path.as_posix(), cv2.IMREAD_COLOR)
        img = _resize1(img)
        if padding_mode == "black":
            img, _ = _pad_black(img)
        elif padding_mode == "full":
            img = _pad_full(img)
        elif padding_mode == "full_darker":
            img = _pad_full_darker(img)
        elif padding_mode == "full_blurred":
            img = _pad_full_blurred(img)
        else:
            raise ValueError("Incorrect padding mode: '{}'".format(padding_mode))
        images.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    return images


def make_video(images: List[np.ndarray], save_path: Union[Path, str], bgm_file: Union[Path, str] = None, each_duration: int = 5) -> Path:
    """Make video from images loaded by `load_images` and bgm from bgm_file(optinal).

    Args:
        images: images loaded by `load_images`, or images in RGB format and the same size.
        save_path: path to save, will auto replace suffix to `.mp4`.
        bgm_file: A audio file to be added to video.
        each_duration: seconds each image should last.
    """

    save_path = Path(save_path).with_suffix(".mp4")
    img_video = mvp.ImageSequenceClip(images, durations=[each_duration]*len(images))
    if bgm_file:
        bgm = mvp.AudioFileClip(Path(bgm_file).as_posix())
        bgm = bgm.set_duration(img_video.duration).audio_fadein(1).audio_fadeout(3)
        img_video = img_video.set_audio(bgm)
    img_video.write_videofile(save_path.as_posix(), fps=24)
    img_video.close()
    return save_path


def img_add_salt(img_path: PathLike, save_path: PathLike = None, *, random_salt: bool = False) -> bool:
    """Add salt to img. 

    If save_path is not given, will overwrite the previous img file.
    """

    img_path = Path(img_path)

    img_hash = hashlib.sha256(img_path.read_bytes()).digest()

    if random_salt:
        rnd = np.random.RandomState(np.random.MT19937(int.from_bytes(img_hash + secrets.token_bytes(32), "big")))
    else:
        rnd = np.random.RandomState(np.random.MT19937(int.from_bytes(img_hash, "big")))

    img: np.ndarray = cv2.imread(img_path.as_posix(), cv2.IMREAD_UNCHANGED)
    if not isinstance(img, np.ndarray):
        return False

    salt_mask = rnd.randint(2, size=img.shape, dtype=img.dtype)
    img = np.bitwise_xor(img, salt_mask)

    if not save_path:
        save_path = img_path
    save_path = Path(save_path)

    cv2.imwrite(save_path.as_posix(), img)
    return True


def make_blacktank(img_path: PathLike, save_path: PathLike) -> Path:
    """Hide image info into alpha channel. Return save_path if success, else None."""
    img = cv2.imread(Path(img_path).as_posix(), cv2.IMREAD_GRAYSCALE)
    if isinstance(img, np.ndarray):
        img_black = np.zeros(img.shape, dtype=np.uint8)
        img_alpha = 255 - img
        img_out = np.stack([img_black, img_black, img_black, img_alpha], axis=2)

        save_path = Path(save_path).with_suffix(".png")
        cv2.imwrite(save_path.as_posix(), img_out)
        return save_path
    else:
        return None
