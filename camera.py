import numpy as np
from typing import Tuple

class Camera:
    """
    简单透视相机，包含内参和外参
    """
    def __init__(self,
                 fx: float, fy: float,
                 cx: float, cy: float,
                 width: int, height: int,
                 pose: np.ndarray = None):
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
        self.width = width
        self.height = height
        if pose is None:
            self.pose = np.eye(4, dtype=np.float32)
        else:
            self.pose = pose.astype(np.float32)
    
    def resize(self, width: int, height: int) -> 'Camera':
        new_width = int(width)
        new_height = int(height)
        if new_width <= 0 or new_height <= 0:
            raise ValueError("width and height must be positive integers")

        scale = min(new_width / self.width, new_height / self.height)
        fx = self.fx * scale
        fy = self.fy * scale
        cx = self.cx * scale
        cy = self.cy * scale
        return Camera(fx, fy, cx, cy, new_width, new_height, pose=self.pose)

    def set_pose(self, pose: np.ndarray, world_to_camera: bool = True, coord_type: str = "opencv"):
        assert pose.shape == (4, 4)
        self.pose = pose.astype(np.float32)
        if not world_to_camera:
            self.pose = np.linalg.inv(self.pose)

        if coord_type == "opencv":
            pass
        elif coord_type == "opengl" or coord_type == "blender":
            self.pose[:3, 1:3] *= -1
        elif coord_type == "pytorch3d":
            self.pose[:3, :3] = self.pose[:3, :3].T
            self.pose[:3, :2] *= -1
        else:
            raise ValueError(f"Invalid coordinate type: {coord_type}")

    def get_pose(self, world_to_camera: bool = True, coord_type: str = "opencv") -> np.ndarray:
        """
        获取相机外参，world_to_camera 为 True 时返回世界到相机的变换矩阵，为 False 时返回相机到世界的变换矩阵
        """
        w2c = self.pose.copy()
        c2w = np.linalg.inv(w2c)
        if coord_type == "opencv":
            pass
        elif coord_type == "opengl" or coord_type == "blender":
            c2w[:3, 1:3] *= -1
            w2c = np.linalg.inv(c2w)
        elif coord_type == "pytorch3d":
            w2c[:2] *= -1
            w2c[:3, :3] = w2c[:3, :3].T
            c2w = np.linalg.inv(w2c)
        else:
            raise ValueError(f"Invalid coordinate type: {coord_type}")

        if world_to_camera:
            return w2c
        else:
            return c2w

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
        self.pose = self.pose @ Ry @ Rx

    def get_intrinsics(self) -> np.ndarray:
        K = np.array([
            [self.fx,       0, self.cx],
            [      0, self.fy, self.cy],
            [      0,       0,       1]
        ], dtype=np.float32)
        return K