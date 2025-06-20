import numpy as np
from typing import List, Tuple, Union
# import cppimport
# import os
import cv2


# _C = cppimport.imp("webviewer.gl.line.image_draw")

def draw_lines(
        image: np.ndarray,
        lines: List[List[int]],
        color: Union[Tuple[int], int]
):
    # check
    if not isinstance(image, np.ndarray):
        raise ValueError("image must be ndarray")

    if image.dtype != np.uint8:
        raise ValueError("image must be uint8")
    
    if len(image.shape) != 2 and len(image.shape) != 3:
        raise ValueError("image must be 2D or 3D")
    
    if not isinstance(color, tuple) and not isinstance(color, list):
        color = [color]
    
    if not isinstance(lines, np.ndarray):
        raise ValueError("lines must be a np.ndarray")
    if len(lines.shape) != 2:
        raise ValueError("lines must be a 2D array")
    
    if lines.shape[1] != 4:
        raise ValueError("lines must be a [N, 4] array")

    # _C.draw_lines(image, lines, color)
    for line in lines.astype(np.int32):
        cv2.line(image, (line[0], line[1]), (line[2], line[3]), color, 1, cv2.LINE_AA)
    
