from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import copy
import json
import cv2
import numpy as np
import io
import threading
import time
import hashlib
from typing import Optional, Union, Callable, List, Dict, Tuple
from abc import ABC, abstractmethod
from .controls import *
from .utils import *
import uuid


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
        ):
        self._sid = sid

        print("new", self._sid)
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
    
    def _set_controls(self, controls: List[Tuple[str, BasicControl]], copy: bool):
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

        if width is None and height is None:
            if not isinstance(width, int) or (width <= 0):
                raise ValueError("Width must be a positive integer")
            
            if not isinstance(height, int) or (height <= 0):
                raise ValueError("Height must be a positive integer")

            if self.image_width != width or self.image_height != height:
                self.image_width = width
                self.image_height = height

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

    def start(self, socketio, render_func):
        render_time = 0

        # wait for canvas init
        while True:
            if self.image_width is not None and self.image_height is not None:
                break
            else:
                time.sleep(0.2)

        print("init succeed!")
        
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


class BaseWebViewer(ABC):
    
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None):
        self.image_width = width
        self.image_height = height
        
        self._app = Flask(__name__)
        self._socketio = SocketIO(self._app)
        
        self._controls: List[Tuple[str, BasicControl]] = []

        self._connect_num = 0
        self._sessions = dict()
        self._shared_session: Session = None

        self._target_fps = 60

        self._force_fix_aspect_ratio = True
        self._use_dynamic_resolution = True
        self._min_pixel              = None
        self._max_pixel              = None
        self._adjustment_step        = None

        @self._app.route('/')
        def index():
            return render_template('index.html')
        
    def set_target_fps(self, fps: float):
        self._target_fps = fps
    
    def get_target_fps(self) -> float:
        return self._target_fps
    
    def set_force_fix_aspect_ratio(self, is_force_fix_aspect_ratio: bool):
        self._force_fix_aspect_ratio = is_force_fix_aspect_ratio
        
    def set_fixed_resolution(
            self,
            width : Optional[int] = None,
            height: Optional[int] = None,
        ):
        self._use_dynamic_resolution = False
        self._image_width            = width
        self._image_height           = height
        
    def set_dynamic_resolution(
            self,
            min_pixel:       Optional[int]   = None,
            max_pixel:       Optional[int]   = None,
            adjustment_step: Optional[float] = None,
        ) -> None: 
        self._use_dynamic_resolution = True
        self._min_pixel              = min_pixel
        self._max_pixel              = max_pixel
        self._adjustment_step        = adjustment_step
        
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
        pass

    def on_left_mouse_release(self, session: Session):
        pass
    
    def on_right_mouse_press(self, session: Session):
        pass

    def on_right_mouse_release(self, session: Session):
        pass
    
    def on_mouse_move(self, session: Session):
        pass
    
    def on_mouse_wheel(self, session: Session, delta):
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

    # Controls
    def add_control(self, name: str, control: BasicControl) -> None:
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
        
        self._controls.append((name, control))
    
    def get_control(self, name: str) -> BasicControl:
        session = self._get_current_session()
        
        return session.get_control(name)

    def add_button(
            self, 
            name:     str,
            text:     str,
            callback: Callable[[dict], None],
        ) -> None:
        
        control = Button(text, callback)
        
        self.add_control(name, control)
    
    def add_slider(
            self,
            name:       str,
            text:       str,
            callback:   Callable[[dict], None],
            init_value: Union[int, float],
            min:        Union[int, float],
            max:        Union[int, float],
            step:       Union[int, float],
        ) -> None:

        control = Slider(
            text, callback, init_value, min, max, step
        )
        
        self.add_control(name, control)

    def add_text(
            self, 
            name: str,
            text: str,
        ) -> None:
        
        control = Text(text)
        
        self.add_control(name, control)

    def add_dropdown(
            self,
            name:        str,
            text:        str,
            init_option: str,
            options:     List[str],
            callback:    Callable[[dict], None],
        ) -> None: 
        
        control = Dropdown(text, init_option, options, callback)

        self.add_control(name, control)
    
    def add_divider(self) -> None:
        
        control = Divider()

        self.add_control(None, control)
        
    def add_checkbox(self,
                     name:       str,
                     text:       str,
                     init_value: bool,
                     callback:   Callable[[dict], None],
                     ) -> None:

        control = Checkbox(text, init_value, callback)

        self.add_control(name, control)
    
    def add_accordion(self,
                      name: str,
                      text: str,
                      expanded: bool = True,
    ):
        control = Accordion(text, expanded)

        self.add_control(name, control)
        
        return control

    def add_tab(self, name: str):
        control = Tab()

        self.add_control(name, control)
        
        return control
    
    def add_inputbox(self,
                     name:       str,
                     label:    str,
                     content:  str,
                     desc:     str,
                     callback: Callable[[dict], None],
                     ):
        control = Inputbox(label, content, desc, callback)
        
        self.add_control(name, control)
    
    def add_image(self,
                  name:      str,
                  image:    np.ndarray,
                  callback: Callable[[dict], None] = None):

        control = Image(image, callback)
        
        self.add_control(name, control)

    def _get_current_session(self):
        if self._shared_session is not None:
            return self._shared_session
        else:
            return self._sessions[request.sid]
    
    def _new_default_session(self, sid):
        return Session(
            width                  = self.image_width,
            height                 = self.image_height,
            sid                    = sid,
            force_fix_aspect_ratio = self._force_fix_aspect_ratio,
            use_dynamic_resolution = self._use_dynamic_resolution,
            target_frame_rate      = self._target_fps,
            min_pixel              = self._min_pixel,
            max_pixel              = self._max_pixel,
            adjustment_step        = self._adjustment_step,
        )

    def _init_routes(self, shared_session: bool):
        
        @self._socketio.on('connect')
        def handle_connect():
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

            htmls = []
            contents = []
            for control_name in session._controls_names:
                control = session.get_control(control_name)
                control.set_socketio(self._socketio, sid)
                
                htmls.append(control.get_html())
                for content in control._get_content():
                    contents.append(content)

            htmls = "\n".join(htmls)

            emit('render_controls', {'htmls': htmls, 'contents': contents})
            
            self.on_connect(session)
            

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
            
            self.on_mouse_wheel(session, data['delta'])

        @self._socketio.on('update_mouse_position')
        def handle_udate_mouse_position(data):
            session = self._get_current_session()
            
            session.x = data['x']
            session.y = data['y']
            session.last_x = data['last_x']
            session.last_y = data['last_y']

            self.on_mouse_move(session)
