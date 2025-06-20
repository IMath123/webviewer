from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import copy
import json
import cv2
import numpy as np
import io
import threading
import time
import hashlib
from typing import Optional, Union, Callable, List, Dict, Tuple, Any
from abc import ABC, abstractmethod
from .controls import *
from .utils import *
import uuid
import os
from .camera import Camera


class Session:

    def __init__(
            self,
            width                 : Optional[int] = None,
            height                : Optional[int] = None,
            *,
            sid                   : Optional[str] = None,
            min_pixel             : int           = 256,
            max_pixel             : int           = 1024,
            target_frame_rate     : float         = 60.0,
            adjustment_step       : float         = 0.05,
            use_dynamic_resolution: bool          = True,
            force_fix_aspect_ratio: bool          = True,
            default_theme         : str           = "one-dark",
        ):
        self._sid = sid

        self.image_width     = width
        self.image_height    = height
        self.canvas_width    = None
        self.canvas_height   = None
        self.last_image_hash = None

        self._controls_names = []
        self._controls = {}

        if self.image_height is not None and self.image_width is not None:
            self.render_aspect_ratio = self.image_height / self.image_width
        else:
            self.render_aspect_ratio = 1
        
        self.canvas_aspect_ratio = 1.0

        self.target_frame_rate = target_frame_rate
        self.frame_interval    = 1.0 / self.target_frame_rate
        self.adjustment_step   = adjustment_step

        self.use_dynamic_resolution = use_dynamic_resolution
        self.force_fix_aspect_ratio = force_fix_aspect_ratio

        self.left_mouse_pressing   = False
        self.right_mouse_pressing  = False

        self.min_pixel = min_pixel
        self.max_pixel = max_pixel

        self.x      = 0
        self.y      = 0
        self.last_x = 0
        self.last_y = 0
        
        self.padding_x = 0
        self.padding_y = 0

        self.manually_image_width = None
        self.manually_image_height = None

        self.default_theme = default_theme

        # UI锁定标志，防止重复添加控件
        self._ui_locked = False
        
        # SocketIO实例，用于与前端通信
        self._socketio = None
        
        # 鼠标轨道球交互状态
        self._camera_orbit_dragging = False
        self._camera_last_x = 0
        self._camera_last_y = 0
        # 鼠标右键平移交互状态
        self._camera_pan_dragging = False
        self._camera_pan_last_x = 0
        self._camera_pan_last_y = 0
        # 相机（可选）
        self.camera = None
        # 相机交互控制系数
        self._orbit_sensitivity = 0.01
        self._pan_sensitivity = 0.01
        self._zoom_sensitivity = 0.01
    
    def get_socketio(self):
        return self._socketio
    
    def lock_ui(self):
        """锁定UI，禁止后续添加控件"""
        self._ui_locked = True

    def _check_ui_locked(self):
        return self._ui_locked

    def _set_controls(self, controls: List[Tuple[str, BasicControl]], copy: bool):
        if self._check_ui_locked():
            return
        for name, control in controls:
            if name in self._controls_names:
                raise RuntimeError(f"Control name {name} already exists")
            self._controls_names.append(name)
            self._controls[name] = control.copy() if copy else control
    
    def get_control(self, name: str):
        if not isinstance(name, str):
            raise TypeError("name must be a string")

        control_path = name.split(".")
        control = self._controls[control_path[0]]
        
        for i in range(1, len(control_path)):
            control = control.get_control(control_path[i])

        return control
    
    def __getitem__(self, name: str):
        return self.get_control(name)
        
    def clamp_with_ratio(self, width: int, height: int):
        if self.render_aspect_ratio < 1.0:
            width = int(height / self.render_aspect_ratio)
            
            if width > self.max_pixel:
                width = self.max_pixel
                height = max(self.min_pixel, int(self.max_pixel * self.render_aspect_ratio))
            
            if width < self.min_pixel:
                height = self.min_pixel
                width = min(self.max_pixel, int(self.min_pixel / self.render_aspect_ratio))
        else:
            height = int(width * self.render_aspect_ratio)

            if height > self.max_pixel:
                height = self.max_pixel
                width = max(self.min_pixel, int(self.max_pixel / self.render_aspect_ratio))
            
            if height < self.min_pixel:
                width = self.min_pixel
                height = min(self.max_pixel, int(self.min_pixel * self.render_aspect_ratio))
        
        return width, height

    def adjust_image_size(self, render_time: float):
        if render_time <= 0:
            return
        
        actual_frame_rate = 1.0 / render_time
        ratio = actual_frame_rate / self.target_frame_rate
        if ratio < 1:
            min_scale_factor = self.min_pixel / max(self.image_width, self.image_height)
            scale_factor = max(min_scale_factor, ratio)
        else:
            max_scale_factor = self.max_pixel / min(self.image_width, self.image_height)
            scale_factor = min(max_scale_factor, ratio)

        target_width = int(self.image_width * scale_factor)
        target_height = int(self.image_height * scale_factor)

        new_width = clip(int(self.image_width + (target_width - self.image_width) * self.adjustment_step), self.min_pixel, self.max_pixel)
        new_height = clip(int(self.image_height + (target_height - self.image_height) * self.adjustment_step), self.min_pixel, self.max_pixel)

        new_width, new_height = self.clamp_with_ratio(new_width, new_height)

        if new_width != self.image_width or new_height != self.image_height:
            self.image_width = new_width
            self.image_height = new_height
            
    def get_cursor_position(self):
        return self.x, self.y
    
    def get_cursor_last_position(self):
        return self.last_x, self.last_y
    
    def get_cursor_position_in_pixel(self):
        _x, _y = self.get_cursor_position()
        
        if self.manually_image_height is not None:
            image_width  = self.manually_image_width + 2 * self.padding_x
            image_height = self.manually_image_height + 2 * self.padding_y
        else: 
            image_width  = self.image_width
            image_height = self.image_height
            
        return (_x * image_width / self.canvas_width - self.padding_x,
                _y * image_height / self.canvas_height - self.padding_y)

    def get_canvas_size(self):
        return self.canvas_width, self.canvas_height

    def is_left_mouse_pressing(self):
        return self.left_mouse_pressing
    
    def is_right_mouse_pressing(self):
        return self.right_mouse_pressing
    
    def set_target_fps(self, fps: float):
        if not isinstance(fps, float) or (fps <= 0):
            raise ValueError("FPS must be a positive float")
        
        self.target_frame_rate = fps
        self.frame_interval = 1.0 / self.target_frame_rate
    
    def get_target_fps(self) -> float:
        return self.target_frame_rate
    
    def set_force_fix_aspect_ratio(self, is_force_fix_aspect_ratio: bool):
        if not isinstance(is_force_fix_aspect_ratio, bool):
            raise RuntimeError("set_force_fix_aspect_ratio takes a bool as input")
        
        self.force_fix_aspect_ratio = is_force_fix_aspect_ratio
        
    def set_fixed_resolution(
            self,
            width : Optional[int] = None,
            height: Optional[int] = None,
        ):
        
        self.use_dynamic_resolution = False

        if width is not None:
            if not isinstance(width, int) or (width <= 0):
                raise ValueError("Width must be a positive integer")
            self.image_width = width
            
        if height is not None:
            if not isinstance(height, int) or (height <= 0):
                raise ValueError("Height must be a positive integer")
            self.image_height = height

        # 调用前端resizeCanvas函数
        if hasattr(self, '_socketio') and self._socketio is not None:
            self._socketio.emit('resize_canvas', room=self._sid)

    def set_dynamic_resolution(
            self,
            min_pixel:       Optional[int]   = None,
            max_pixel:       Optional[int]   = None,
            adjustment_step: Optional[float] = None,
        ) -> None: 

        self.use_dynamic_resolution = True
        
        if min_pixel is not None:
            if not isinstance(min_pixel, int) or min_pixel < 1:
                raise ValueError("min_pixel must be an integer greater than or equal to 1")

            self.min_pixel = min_pixel
        
        if max_pixel is not None:
            if not isinstance(max_pixel, int) or max_pixel < min_pixel:
                raise ValueError("max_pixel must be an integer greater than or equal to min_pixel")

            self.max_pixel = max_pixel
        
        if adjustment_step is not None:
            if not isinstance(adjustment_step, float) or adjustment_step < 1e-3:
                raise ValueError("adjustment_step must be a float greater than or equal to 1e-3")
            
            self.adjustment_step = adjustment_step

        # 调用前端resizeCanvas函数
        if hasattr(self, '_socketio') and self._socketio is not None:
            self._socketio.emit('resize_canvas', room=self._sid)

    def is_dynamic_resolution_enabled(self) -> bool:
        """判断是否启用了动态分辨率"""
        return self.use_dynamic_resolution
    
    def get_dynamic_resolution_params(self) -> dict:
        """获取动态分辨率的参数"""
        return {
            'use_dynamic_resolution': self.use_dynamic_resolution,
            'min_pixel': self.min_pixel,
            'max_pixel': self.max_pixel,
            'adjustment_step': self.adjustment_step
        }
    
    def is_fixed_aspect_ratio_enabled(self) -> bool:
        """判断是否启用了固定长宽比"""
        return self.force_fix_aspect_ratio

    def start(self, socketio, render_func):
        # 设置SocketIO实例
        self._socketio = socketio
        
        render_time = 0

        # wait for canvas init
        while True:
            if self.image_width is not None and self.image_height is not None:
                break
            else:
                time.sleep(0.1)

        while True:
            frame_start_time = time.time()
            
            if self.use_dynamic_resolution:
                self.adjust_image_size(render_time)

            current_image_width = self.image_width
            current_image_height = self.image_height

            if self.force_fix_aspect_ratio:
                max_pixel = max(
                    current_image_height,
                    current_image_width * self.canvas_aspect_ratio,
                )
                
                padding_x = max(0, int((max_pixel / self.canvas_aspect_ratio - current_image_width) / 2))
                padding_y = max(0, int((max_pixel - current_image_height) / 2))
            else:
                padding_x = 0
                padding_y = 0

            if current_image_width is not None and current_image_height is not None:
                try:
                    image = render_func(width=current_image_width, height=current_image_height, session=self)
                except NotImplementedError as e:
                    break
                
                if image is not None:
                    self.padding_x = padding_x
                    self.padding_y = padding_y
                    
                    if padding_x > 0 or padding_y > 0:
                        image = np.pad(image, ((padding_y, padding_y), (padding_x, padding_x), (0, 0)), 'constant', constant_values=0)

                    _, buf = cv2.imencode('.jpg', image)
                    img_data = buf.tobytes()
                    # 使用room参数指定接收者
                    if self._sid is not None:
                        socketio.emit('draw_response', img_data, room=self._sid)
                    else:
                        socketio.emit('draw_response', img_data)

                else:
                    time.sleep(0.1)
                    render_time = 0
                    continue

            render_time = time.time() - frame_start_time
            sleep_time = max(0, self.frame_interval - render_time)
            time.sleep(sleep_time)

    def add_control(self, name: str, control: BasicControl) -> None:
        if self._check_ui_locked():
            return
        if name is None:
            name = str(uuid.uuid4())
        if not isinstance(name, str):
            raise TypeError('name must be a string')
        if not isinstance(control, BasicControl):
            raise TypeError('control must be a subclass of BasicControl')
        if len(name) == 0:
            raise ValueError('name must not be empty')
        if "." in name:
            raise ValueError("name must not contain '.'")
        self._controls_names.append(name)
        self._controls[name] = control

    def add_button(self, name: str, text: str, callback: Callable[[BasicControl], None]) -> None:
        control = Button(text, callback)
        self.add_control(name, control)

    def add_slider(self, name: str, text: str, callback: Callable[[BasicControl], None], init_value: Union[int, float], min: Union[int, float], max: Union[int, float], step: Union[int, float]) -> None:
        """添加滑块控件"""
        from .controls.slider import Slider
        control = Slider(text, callback, init_value, min, max, step)
        self.add_control(name, control)

    def add_text(self, name: str, text: str, 
                 wrap: bool = True, 
                 max_lines: Optional[int] = None, 
                 show_line_numbers: bool = False, 
                 color: Optional[str] = None,
                 align: Optional[str] = None,
                 font_size: Optional[str] = None,
                 bold: bool = False,
                 italic: bool = False,
                 underline: bool = False,
                 shadow: Optional[str] = None,
                 line_height: Optional[str] = None
                 ) -> None:
        """添加文本控件"""
        from .controls.text import Text
        control = Text(
            text, wrap=wrap, max_lines=max_lines, show_line_numbers=show_line_numbers, color=color,
            align=align, font_size=font_size, bold=bold, italic=italic, underline=underline, shadow=shadow, line_height=line_height
        )
        self.add_control(name, control)

    def add_dropdown(self, name: str, text: str, init_option: str, options: List[str], callback: Callable[[BasicControl], None]) -> None:
        """添加下拉选择控件"""
        from .controls.dropdown import Dropdown
        control = Dropdown(text, init_option, options, callback)
        self.add_control(name, control)

    def add_divider(self) -> None:
        control = Divider()
        self.add_control(str(uuid.uuid4()), control)

    def add_checkbox(self, name: str, text: str, init_value: bool, callback: Callable[[BasicControl], None]) -> None:
        control = Checkbox(text, init_value, callback)
        self.add_control(name, control)

    def add_accordion(self, name: str, text: str, expanded: bool = True):
        control = Accordion(text, expanded)
        self.add_control(name, control)
        return control

    def add_tab(self, name: str):
        control = Tab()
        self.add_control(name, control)
        return control

    def add_inputbox(self, name: str, label: str, content: str, desc: str, callback: Callable[[BasicControl], None]):
        control = Inputbox(label, content, desc, callback)
        self.add_control(name, control)

    def add_image(self, name: str, image: np.ndarray, callback: Callable[[BasicControl], None] = None):
        """添加图像控件"""
        from .controls.image import Image
        control = Image(image, callback)
        self.add_control(name, control)

    def add_theme_selector(self, callback: Callable[[BasicControl], None] = None):
        """添加主题切换控件"""
        from .controls.dropdown import ThemeDropdown
        control = ThemeDropdown(init_option=self.default_theme, callback=callback)
        self.add_control("theme_dropdown", control)

    def add_progress(self, name: str, text: str, callback: Callable[[BasicControl], None], init_value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float], step: Union[int, float]) -> None:
        """添加进度条控件"""
        from .controls.progress import Progress
        control = Progress(text, init_value, min_value, max_value, callback)
        self.add_control(name, control)

    def add_colorpicker(self, name: str, text: str, callback: Callable[[BasicControl], None], init_color: str = "#000000") -> None:
        """添加颜色选择器控件"""
        from .controls.colorpicker import ColorPicker
        control = ColorPicker(text, init_color, callback)
        self.add_control(name, control)

    def add_table(self, name: str, text: str, callback: Callable[[BasicControl], None], headers: List[str], data: List[List[str]], selectable: bool = False, sortable: bool = False) -> None:
        """添加数据表格控件"""
        from .controls.table import Table
        control = Table(text, headers, data, callback, sortable, selectable)
        self.add_control(name, control)
    
    def add_container(self,
                      name: str,
                      direction: str = "vertical",
                      gap: str = "10px",
                      padding: str = "15px",
                      callback: Optional[Callable[['Container'], None]] = None) -> 'Container':
        """添加容器控件"""
        # 验证direction参数
        if not isinstance(direction, str):
            raise TypeError("direction must be a string")
        if direction not in ["vertical", "horizontal"]:
            raise ValueError("direction must be either 'vertical' or 'horizontal'")
        
        # 验证gap参数
        if not isinstance(gap, str):
            raise TypeError("gap must be a string")
        if not gap.strip():
            raise ValueError("gap cannot be empty")
        
        # 验证padding参数
        if not isinstance(padding, str):
            raise TypeError("padding must be a string")
        if not padding.strip():
            raise ValueError("padding cannot be empty")
        
        # 验证callback参数
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")
        
        from .controls.container import Container
        container = Container(direction, gap, padding, callback)
        self.add_control(name, container)
        return container

    def enable_camera(self, 
                      width: int, height: int, 
                      *,
                      intrinsics: Optional[np.ndarray] = None,
                      fx: Optional[float] = None, fy: Optional[float] = None,
                      cx: Optional[float] = None, cy: Optional[float] = None, 
                      z_near: Optional[float] = None, z_far: Optional[float] = None,
                      w2c: Optional[np.ndarray] = None,
                      c2w: Optional[np.ndarray] = None,
                      ):
        """启用相机功能，必须提供内参，外参可选"""
        try:
            width = int(width)
            height = int(height)
            if width <= 0 or height <= 0:
                raise ValueError("width and height must be positive integers")
        except (TypeError, ValueError):
            raise TypeError("width and height must be convertible to integers")
        
        if intrinsics is None:
            # 验证焦距参数 - 使用更宽松的类型判断
            try:
                fx = float(fx)
                fy = float(fy)
                cx = float(cx)
                cy = float(cy)
            except (TypeError, ValueError):
                raise TypeError("fx, fy, cx, cy must be convertible to numbers; width, height must be convertible to integers")
            
            if fx <= 0 or fy <= 0:
                raise ValueError("fx and fy must be positive numbers")
            
            # 验证主点是否在图像范围内
            if cx < 0 or cx >= width:
                raise ValueError(f"cx ({cx}) must be in range [0, {width})")
            if cy < 0 or cy >= height:
                raise ValueError(f"cy ({cy}) must be in range [0, {height})")
        else:
            # 验证内参矩阵
            if not isinstance(intrinsics, np.ndarray):
                raise TypeError("intrinsics must be a numpy array")
            if intrinsics.shape != (3, 3):
                raise ValueError("intrinsics must be a 3x3 matrix")
            if intrinsics.dtype != np.float32:
                intrinsics = intrinsics.astype(np.float32)

            fx = intrinsics[0, 0]
            fy = intrinsics[1, 1]
            cx = intrinsics[0, 2]
            cy = intrinsics[1, 2]
        
        from .camera import Camera
        self.camera = Camera(fx, fy, cx, cy, width, height, z_near=z_near, z_far=z_far)
        self.camera._update_params(w2c=w2c, c2w=c2w)

    def _on_mouse_move(self):
        """内部鼠标移动处理逻辑"""
        if self.camera is None:
            return
        # 处理轨道球旋转
        if self._camera_orbit_dragging:
            x, y = self.get_cursor_position()
            dx = x - self._camera_last_x
            dy = y - self._camera_last_y
            self._camera_last_x = x
            self._camera_last_y = y
            pitch = dx * self._orbit_sensitivity
            yaw = dy * self._orbit_sensitivity
            self.camera.rotate(yaw, pitch)
        
        # 处理右键平移
        if self._camera_pan_dragging:
            x, y = self.get_cursor_position()
            dx = x - self._camera_pan_last_x
            dy = y - self._camera_pan_last_y
            self._camera_pan_last_x = x
            self._camera_pan_last_y = y
            
            # 相机在自身坐标系 x-y 平面内平移
            step_x = -dx * self._pan_sensitivity
            step_y = dy * self._pan_sensitivity
            pose = self.camera.get_c2w()
            R = pose[:3, :3]
            right = R[:3, 0]  # 相机右方向
            up = -R[:3, 1]     # 相机上方向
            pose[:3, 3] += right * step_x + up * step_y
            self.camera.set_c2w(pose)

    def _on_mouse_wheel(self, delta):
        """内部鼠标滚轮处理逻辑"""
        if self.camera is None:
            return
        # 鼠标滚轮控制缩放：相机沿自身坐标系 -z 方向（视线方向）平移
        step = -float(delta) * self._zoom_sensitivity
        c2w = self.camera.get_c2w()
        R = c2w[:3, :3]
        forward = R[:3, 2]
        c2w[:3, 3] += forward * step
        self.camera.set_c2w(c2w)
       

class BaseWebViewer(ABC):
    
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None, *, title: str = "WebViewer"):
        self.image_width = width
        self.image_height = height
        self._title = title
        
        self._app = Flask(__name__)
        self._socketio = SocketIO(self._app, cors_allowed_origins="*")
        
        self._sessions = {}
        self._shared_session = None
        self._connect_num = 0
        self._controls = {}
        self._controls_names = []
        
        # 默认主题配置
        self._default_theme = "one-dark"  # 可以在子类中修改
        
        @self._app.route('/')
        def index():
            return render_template('index.html', title=self._title)
        
        @self._app.route('/themes/<path:filename>')
        def themes(filename):
            return send_from_directory('templates/themes', filename)
        
    def _clamp_with_ratio(self, session: Session, width: int, height: int):
        return session.clamp_with_ratio(width, height)

    def _adjust_image_size(self, session: Session, render_time: float):
        session.adjust_image_size(render_time)
            
    def is_left_mouse_pressing(self):
        session = self._get_current_session()
        return session.left_mouse_pressing
    
    def is_right_mouse_pressing(self):
        session = self._get_current_session()
        return session.right_mouse_pressing
    
    # interactivate
    def on_connect(self, session: Session):
        pass
    
    def on_left_mouse_press(self, session: Session):
        if session.camera is None:
            return
        session._camera_orbit_dragging = True
        session._camera_last_x, session._camera_last_y = session.get_cursor_position()

    def on_mouse_move(self, session: Session):
        pass
        
    def on_left_mouse_release(self, session: Session):
        if session.camera is None:
            return
        if session._camera_orbit_dragging:
            session._camera_orbit_dragging = False

    def on_right_mouse_press(self, session: Session):
        if session.camera is None:
            return
        # 记录右键拖动起点
        session._camera_pan_dragging = True
        session._camera_pan_last_x, session._camera_pan_last_y = session.get_cursor_position()

    def on_right_mouse_release(self, session: Session):
        if session.camera is None:
            return
        if session._camera_pan_dragging:
            session._camera_pan_dragging = False

    def on_mouse_wheel(self, session: Session, delta):
        """处理鼠标滚轮事件，用户可以重写此方法"""
        pass

    def render(self, image_width: int, image_height: int, session: Session, **kwargs) -> np.ndarray:
        raise NotImplementedError("Subclasses must implement this method")  
    
    def manully_render(self):
        return None
    
    def get_connect_num(self):
        return self._connect_num

    def get_current_session(self):
        return self._get_current_session()

    def run(self,
            host:            str  = '0.0.0.0',
            port:            int  = 5001,
            shared_session:  bool = False,
            manually_render: bool = False,
        ):

        self._init_routes(shared_session)

        self._socketio.run(self._app, debug=False, host=host, port=port)
        
        # reset
        self._shared_session = None
        self._connect_num = 0

    def _get_current_session(self):
        if self._shared_session is not None:
            return self._shared_session
        else:
            return self._sessions[request.sid]
    
    def _new_default_session(self, sid):
        return Session(
            width         = self.image_width,
            height        = self.image_height,
            sid           = sid,
            default_theme = self._default_theme
        )

    def _init_routes(self, shared_session: bool):
        
        @self._socketio.on('connect')
        def handle_connect(auth=None):
            self._connect_num += 1

            sid = request.sid
            
            # 将客户端加入到以其sid为名的room
            # join_room(sid)

            if shared_session:
                if self._shared_session is None:
                    session = self._new_default_session(None)
                    self._shared_session = session
                    session._set_controls(self._controls, copy=False)
                    threading.Thread(target=session.start, args=(self._socketio, self.render)).start()
                else:
                    session = self._shared_session
            else:
                session = self._new_default_session(sid)
                session._set_controls(self._controls, copy=True)
                self._sessions[sid] = session
                threading.Thread(target=session.start, args=(self._socketio, self.render)).start()

            self.on_connect(session)
            
            htmls = []
            contents = []
            for control_name in session._controls_names:
                control = session.get_control(control_name)
                control.set_socketio(self._socketio, sid)
                
                htmls.append(control.get_html())
                for content in control._get_content():
                    contents.append(content)

            htmls = "\n".join(htmls)

            # 添加设置默认主题的JavaScript代码
            default_theme_script = f'<script>setTheme("theme-{self._default_theme}");</script>'
            htmls += default_theme_script

            emit('render_controls', {'htmls': htmls, 'contents': contents})

            session.lock_ui()
            

        @self._socketio.on('disconnect')
        def handle_disconnect():
            sid = request.sid

            if sid in self._sessions:
                # leave_room(sid)
                del self._sessions[sid]
                
            self._connect_num -= 1
            
            if self._connect_num < 0:
                self._connect_num = 0

        @self._socketio.on('set_image_size_by_canvas_size')
        def handle_set_image_size_by_canvas_size(data):
            session = self._get_current_session()
            
            if session.image_height is None and session.image_width is None:
                session.image_height = data["height"]
                session.image_width = data["width"]
                session.render_aspect_ratio = session.image_height / session.image_width
        
        @self._socketio.on('send_canvas_size')
        def handle_send_canvas_size(data):
            session = self._get_current_session()
            
            session.canvas_width = data["canvas_width"]
            session.canvas_height = data["canvas_height"]
            session.canvas_aspect_ratio = session.canvas_height / session.canvas_width

        @self._socketio.on('set_aspect_ratio')
        def handle_set_aspect_ratio(data):
            session = self._get_current_session()
            
            session.canvas_aspect_ratio = data['aspect_ratio']

            if not session.force_fix_aspect_ratio:
                session.render_aspect_ratio = session.canvas_aspect_ratio
            
            if session.image_height is None or session.image_width is None:
                return
            
            if session.use_dynamic_resolution:
                min_pixel = min(session.image_width, session.image_height)
                if session.render_aspect_ratio < 1.0:
                    target_height = min_pixel
                    target_width = int(target_height / session.render_aspect_ratio)
                else:
                    target_width = min_pixel
                    target_height = int(target_width * session.render_aspect_ratio)
                
                session.image_width = target_width
                session.image_height = target_height
            else:
                pass
            
        @self._socketio.on('on_left_mouse_press')
        def handle_left_mouse_press():
            session = self._get_current_session()
            
            session.left_mouse_pressing = True
            self.on_left_mouse_press(session)

        @self._socketio.on('on_left_mouse_release')
        def handle_left_mouse_release():
            session = self._get_current_session()
            
            session.left_mouse_pressing = False
            self.on_left_mouse_release(session)

        @self._socketio.on('on_right_mouse_press')
        def handle_right_mouse_press():
            session = self._get_current_session()
            
            session.right_mouse_pressing = True
            self.on_right_mouse_press(session)

        @self._socketio.on('on_right_mouse_release')
        def handle_right_mouse_release():
            session = self._get_current_session()
            
            session.right_mouse_pressing = False
            self.on_right_mouse_release(session)

        @self._socketio.on('on_mouse_wheel')
        def handle_on_mouse_wheel(data):
            session = self._get_current_session()
            
            # 先调用内部鼠标滚轮处理逻辑
            session._on_mouse_wheel(data['delta'])
            # 再调用用户自定义的鼠标滚轮处理逻辑
            self.on_mouse_wheel(session, data['delta'])

        @self._socketio.on('update_mouse_position')
        def handle_udate_mouse_position(data):
            session = self._get_current_session()
            
            session.x = data['x']
            session.y = data['y']
            session.last_x = data['last_x']
            session.last_y = data['last_y']

            # 先调用内部鼠标处理逻辑
            session._on_mouse_move()
            # 再调用用户自定义的鼠标处理逻辑
            self.on_mouse_move(session)

        # ListBox控件事件分发
        for name, control in self._controls.items():
            if hasattr(control, 'TYPE') and getattr(control, 'TYPE', None) == 'listbox':
                @self._socketio.on(name)
                def handle_listbox_event(data, name=name, control=control):
                    selected = data.get('selected', [])
                    control.update(selected=selected)
                    if control.callback:
                        control.callback(control)
                    self._send_update(name, {'selected': control.selected})

    def set_default_theme(self, theme: str):
        """设置默认主题"""
        # 检查themes目录
        themes_dir = os.path.join(os.path.dirname(__file__), 'templates', 'themes')
        if not os.path.exists(themes_dir):
            raise ValueError(f"Themes directory not found: {themes_dir}")
        
        # 获取所有可用的主题文件
        theme_files = [f for f in os.listdir(themes_dir) if f.startswith('theme-') and f.endswith('.css')]
        available_themes = [f[len('theme-'):-len('.css')] for f in theme_files]
        
        # 检查输入的theme是否有效
        if theme not in available_themes:
            raise ValueError(f"Theme '{theme}' not found. Available themes: {available_themes}")
        
        self._default_theme = theme
