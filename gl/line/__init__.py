import numpy as np
from typing import List, Tuple, Union
import cppimport
import os


_C = cppimport.imp("webviewer.gl.line.image_draw")

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

    _C.draw_lines(image, lines, color)
