# -*- coding: UTF-8 -*-

import cv2
import numpy as np


def img_recognize(img: np.ndarray) -> str:
    """Used to recognize simple characters from captcha
    """
    cv2.imwrite("./tmp/captcha.jpg", img)
    code = input("Enter Captcha: ")
    return code
