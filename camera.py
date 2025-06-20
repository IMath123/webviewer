import numpy as np
from typing import Tuple, Optional
import math

def fov2focal(fov, pixels):
    return pixels / (2 * math.tan(fov / 2))

def focal2fov(focal, pixels):
    return 2*math.atan(pixels/(2*focal))

class Camera:
    """
    简单透视相机，包含内参和外参
    """
    def __init__(self,
                 fx: float, fy: float,
                 cx: float, cy: float,
                 width: int, height: int,
                 z_near: Optional[float] = None,
                 z_far: Optional[float] = None):
        """
        fx, fy: 焦距
        cx, cy: 主点
        width, height: 图像尺寸
        pose: 4x4 世界到相机的变换矩阵（外参）
        """
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.image_width = width
        self.image_height = height

        if z_near is None:
            z_near = 0.01
        if z_far is None:
            z_far = 100.0

        self.z_near = z_near
        self.z_far = z_far

        self.c2w = np.eye(4, dtype=np.float32)
        self.w2c = np.eye(4, dtype=np.float32)
        self._update_params()
    
    def _update_params(self, *,
                       c2w: Optional[np.ndarray] = None,
                       w2c: Optional[np.ndarray] = None,
                       fx: Optional[float] = None,
                       fy: Optional[float] = None,
                       cx: Optional[float] = None,
                       cy: Optional[float] = None,
                       image_width: Optional[int] = None,
                       image_height: Optional[int] = None):
        # c2w和w2c只能有一个非None，否则报错
        if c2w is not None and w2c is not None:
            raise ValueError("c2w and w2c cannot be both non-None")
        
        if c2w is not None:
            self.c2w = c2w.astype(np.float32)
            self.w2c = np.linalg.inv(self.c2w)
        if w2c is not None:
            self.w2c = w2c.astype(np.float32)
            self.c2w = np.linalg.inv(self.w2c)

        if fx is not None:
            self.fx = fx
        if fy is not None:
            self.fy = fy
        if cx is not None:
            self.cx = cx
        if cy is not None:
            self.cy = cy

        if image_width is not None:
            self.image_width = image_width
        if image_height is not None:
            self.image_height = image_height

        self._intrinsics = np.array([
            [self.fx,       0, self.cx],
            [      0, self.fy, self.cy],
            [      0,       0,       1]
        ], dtype=np.float32)
        
        self.camera_center = self.c2w[:3, 3]
        self.FoVx = focal2fov(self.fx, self.image_width)
        self.FoVy = focal2fov(self.fy, self.image_height)

    def resize(self, width: int, height: int) -> 'Camera':
        new_width = int(width)
        new_height = int(height)
        if new_width <= 0 or new_height <= 0:
            raise ValueError("width and height must be positive integers")

        scale = min(new_width / self.image_width, new_height / self.image_height)
        fx = self.fx * scale
        fy = self.fy * scale
        cx = self.cx * scale
        cy = self.cy * scale
        resized_cam = Camera(fx, fy, cx, cy, new_width, new_height, z_near=self.z_near, z_far=self.z_far)
        resized_cam.set_c2w(self.c2w)
        return resized_cam
    
    def set_c2w(self, c2w: np.ndarray):
        self._update_params(c2w=c2w)
    
    def set_w2c(self, w2c: np.ndarray):
        self._update_params(w2c=w2c)

    def get_c2w(self):
        return self.c2w.copy()
    
    def get_w2c(self):
        return self.w2c.copy()

    def rotate(self, yaw: float, pitch: float):
        """
        绕Y轴（yaw）和X轴（pitch）旋转，单位为弧度
        """
        Ry = np.array([
            [np.cos(yaw), 0, np.sin(yaw), 0],
            [0, 1, 0, 0],
            [-np.sin(yaw), 0, np.cos(yaw), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(pitch), -np.sin(pitch), 0],
            [0, np.sin(pitch), np.cos(pitch), 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        self._update_params(w2c=self.w2c @ Ry @ Rx)

    def get_intrinsics(self) -> np.ndarray:
        return self._intrinsics.copy()