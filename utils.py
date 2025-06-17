import numpy as np
# import torch  # 暂时注释掉torch导入
import time
import random
import string
import math
from .gl.line import draw_lines
from dataclasses import dataclass
from typing import Any, Optional, Union


def project_to_sphere(x, y, radius=1.0):
    """
    将鼠标的 2D 坐标 (x, y) 投影到一个半径为 1 的虚拟球上。
    """
    dist = x**2 + y**2
    if dist <= radius**2:
        # z = torch.sqrt(torch.tensor(radius**2 - dist))  # 在球内
        z = math.sqrt(radius**2 - dist)  # 在球内
    else:
        # z = torch.tensor(0.0)  # 在球外，投影到球面
        z = 0.0  # 在球外，投影到球面
    # return torch.tensor([x, y, z])
    return np.array([x, y, z])

def quaternion_multiply(q1, q2):
    """
    两个四元数的乘法，返回新四元数。
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    # return torch.tensor([w, x, y, z], dtype=torch.float32)
    return np.array([w, x, y, z], dtype=np.float32)

def quaternion_to_matrix(q):
    """
    将四元数转换为 3x3 的旋转矩阵。
    """
    w, x, y, z = q
    # return torch.tensor([
    #     [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
    #     [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
    #     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
    # ], dtype=torch.float32)
    return np.array([
        [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
    ], dtype=np.float32)


def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def look_at(eye, at, up):
    forward = normalize(at - eye)
    right = normalize(np.cross(up, forward))
    up = np.cross(forward, right)

    # get w2c
    result = np.eye(4)
    result[:-3, 0] = right
    result[:-3, 1] = up
    result[:-3, 2] = forward
    result[:3, 3] = -np.dot(result[:-1, :-1].T, eye)

    return result

    

def fov2focal(fov, pixels):
    return pixels / (2 * math.tan(fov / 2))


def focal2fov(focal, pixels):
    return 2*math.atan(pixels/(2*focal))


def random_string(length: int) -> str:
    current = time.time()
    
    seed = current - int(current)

    random.seed(seed)
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def clip(x, minn, maxx):
    if x < minn: return minn
    if x > maxx: return maxx
    return x


class Camera:

    def __init__(self) -> None:
        
        self.R = np.eye(3)
        self.R_t = np.eye(3)
        self.t = np.zeros(3)
        self.height = 0
        self.width = 0
        self.fx = 0
        self.fy = 0
        self.cx = 0
        self.cy = 0
        self.fov = 60
    
    def set_w2c(self, w2c: np.ndarray):
        if not isinstance(w2c, np.ndarray):
            raise TypeError("w2c must be a numpy array")
        
        if len(w2c.shape) != 2 or w2c.shape[0] != 4 or w2c.shape[1] != 4:
            raise ValueError("w2c must be a 4x4 numpy array")
        
        self.R = w2c[:3, :3]
        self.R_t = self.R.T
        self.t = w2c[:3, 3]
    
    def set_c2w(self, c2w: np.ndarray):
        if not isinstance(c2w, np.ndarray):
            raise TypeError("c2w must be a numpy array")
            
        if len(c2w.shape) != 2 or c2w.shape[0] != 4 or c2w.shape[1] != 4:
            raise ValueError("c2w must be a 4x4 numpy array")
        
        w2c = np.linalg.inv(c2w)

        self.R = w2c[:3, :3]
        self.R_t = self.R.T
        self.t = w2c[:3, 3]
    
    def get_c2w(self) -> np.ndarray:
        T = np.eye(4, dtype=np.float32)
        T[:3, :3] = self.R_t
        T[:3, 3] = -self.R_t @ self.t
        
        return T
    
    def get_w2c(self) -> np.ndarray:
        T = np.eye(4, dtype=np.float32)
        T[:3, :3] = self.R
        T[:3, 3] = self.t
        
        return T
    
    def set_look_at(self, eye: np.ndarray, at: np.ndarray, up: np.ndarray):

        T = look_at(eye, at, up)
        self.R = T[:3, :3]
        self.R_t = self.R.T
        self.t = T[:3, 3]
    
    def set_intrinsic(self, width, height, fx, fy, cx, cy):
        self.width = width
        self.height = height

        self.fx = fx 
        self.fy = fy
        self.cx = cx
        self.cy = cy
        
        self.fov = focal2fov(self.fx, width)
        
    def get_draw_lines(self, render_camera, size=0.1):
        c2w = self.get_c2w()
        ratio = self.width / self.height

        camera_center = c2w[:3, 3]
        
        x_axis = c2w[:3, 0]
        y_axis = c2w[:3, 1]
        z_axis = c2w[:3, 2]
        
        point_00 = camera_center - x_axis * size * ratio - y_axis * size + z_axis * size
        point_01 = camera_center - x_axis * size * ratio + y_axis * size + z_axis * size
        point_10 = camera_center + x_axis * size * ratio - y_axis * size + z_axis * size
        point_11 = camera_center + x_axis * size * ratio + y_axis * size + z_axis * size
        
        points = np.stack([camera_center, point_00, point_01, point_10, point_11])
        
        render_w2c = render_camera.get_w2c()
        fx = render_camera.fx
        fy = render_camera.fy
        cx = render_camera.cx
        cy = render_camera.cy

        points_camera = points @ render_w2c[:3, :3].T + render_w2c[:3, 3]
        
        u = (points_camera[:, 0] / points_camera[:, 2] * fx + cx).astype(int)
        v = (points_camera[:, 1] / points_camera[:, 2] * fy + cy).astype(int)
        
        lines = []
        indexs = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [2, 4], [3, 4], [1, 3]]
        for i, j in indexs:
            lines.append((u[i], v[i], u[j], v[j]))
        
        return lines

@dataclass
class ControlData:
    """控件回调数据类，提供类型安全的访问方法"""
    value: Any
    control_id: str
    control_type: str
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数值"""
        val = self._get_value(key)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数值"""
        val = self._get_value(key)
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串值"""
        val = self._get_value(key)
        return str(val) if val is not None else default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔值"""
        val = self._get_value(key)
        if isinstance(val, bool):
            return val
        elif isinstance(val, str):
            return val.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(val, (int, float)):
            return bool(val)
        return default
    
    def get_list(self, key: str, default: list = None) -> list:
        """获取列表值"""
        if default is None:
            default = []
        val = self._get_value(key)
        return list(val) if isinstance(val, (list, tuple)) else default
    
    def _get_value(self, key: str) -> Any:
        """根据键名获取值"""
        # 如果key是'value'，直接返回self.value
        if key == 'value':
            return self.value
        # 如果key是'checked'，对于checkbox控件返回self.value
        elif key == 'checked' and self.control_type == 'checkbox':
            return self.value
        # 如果key是'option'，对于dropdown控件返回self.value
        elif key == 'option' and self.control_type == 'dropdown':
            return self.value
        # 如果key是'content'，对于inputbox控件返回self.value
        elif key == 'content' and self.control_type == 'inputbox':
            return self.value
        # 其他情况返回None
        return None
