from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import copy
import json
import cv2
import numpy as np
import io
import threading
import time
import hashlib
from typing import Optional, Union, Callable, List, Dict
from abc import ABC, abstractmethod
from .controls import *
from .utils import *


class Session:

    def __init__(self):

        self.image_width     = None
        self.image_height    = None
        self.canvas_width    = None
        self.canvas_height   = None
        self.last_image_hash = None

        self.controls = []

        self.aspect_ratio      = 1
        self.target_frame_rate = 60
        self.frame_interval    = 1.0 / self.target_frame_rate
        self.adjustment_step   = 0.05

        self.use_dynamic_resolution = True
        self.force_fix_aspect_ratio = True

        self.left_mouse_pressing   = False
        self.right_mouse_pressing  = False

        self.x      = 0
        self.y      = 0
        self.last_x = 0
        self.last_y = 0
        
        self.min_pixel = 256
        self.max_pixel = 1024

        self.padding_x = 0
        self.padding_y = 0
        self.manually_image_width = None
        self.manually_image_height = None
        
    def clamp_with_ratio(self, width: int, height: int):
        if self.aspect_ratio > 1.0:
            width = int(height * self.aspect_ratio)
            
            if width > self.max_pixel:
                width = self.max_pixel
                height = max(self.min_pixel, int(self.max_pixel / self.aspect_ratio))
            
            if width < self.min_pixel:
                height = self.min_pixel
                width = min(self.max_pixel, int(self.min_pixel * self.aspect_ratio))
        else:
            height = int(width / self.aspect_ratio)

            if height > self.max_pixel:
                height = self.max_pixel
                width = max(self.min_pixel, int(self.max_pixel * self.aspect_ratio))
            
            if height < self.min_pixel:
                width = self.min_pixel
                height = min(self.max_pixel, int(self.min_pixel / self.aspect_ratio))
        
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
        
    def set_fixed_resolution(
            self,
            width:                  Optional[int]  = None,
            height:                 Optional[int]  = None,
            force_fix_aspect_ratio: Optional[bool] = None
        ):
        
        self.use_dynamic_resolution = False

        if isinstance(force_fix_aspect_ratio, bool):
            self.force_fix_aspect_ratio = force_fix_aspect_ratio

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
            adjustment_step: Optional[float] = None
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
            # if not self.is_connecting:
                # time.sleep(0.2)
                # continue

            frame_start_time = time.time()
            if self.use_dynamic_resolution:
                self.adjust_image_size(render_time)

                current_image_width = self.image_width
                current_image_height = self.image_height
                padding_x = 0
                padding_y = 0
            else:
                current_image_height = self.image_height
                current_image_width = self.image_width

                if self.force_fix_aspect_ratio:
                    
                    scale = max(
                        current_image_height,
                        current_image_width / self.aspect_ratio,
                    )
                    
                    padding_x = max(0, int((scale * self.aspect_ratio - current_image_width) / 2))
                    padding_y = max(0, int((scale * 1 - current_image_height) / 2))
                else:
                    padding_x = 0
                    padding_y = 0

            if current_image_width is not None and current_image_height is not None:
                try:
                    image = render_func(current_image_width, current_image_height)
                except NotImplementedError as e:
                    break
                
                if image is not None:
                    rendered_image_height = image.shape[0]
                    rendered_image_width = image.shape[1]

                    self.padding_x = padding_x
                    self.padding_y = padding_y
                    
                    if padding_x > 0 or padding_y > 0:
                        image = np.pad(image, ((padding_y, padding_y), (padding_x, padding_x), (0, 0)), 'constant', constant_values=0)

                else:
                    time.sleep(0.1)
                    render_time = 0
                    continue

            else:
                continue

            if not isinstance(image, np.ndarray):
                raise TypeError("Image must be a numpy array")
            
            if len(image.shape) != 3 and len(image.shape) != 2:
                raise ValueError("Image must have 3 dimensions(H, W, 3/4) or 2 dimensions(H, W)")
            
            if not (rendered_image_height == current_image_height and rendered_image_width == current_image_width):
                raise ValueError("Image dimensions must match the image size")

            _, buf = cv2.imencode('.jpg', image)
            img_data = buf.tobytes()
            # current_image_hash = hashlib.md5(img_data).hexdigest()
            # if current_image_hash != self.last_image_hash:
                # socketio.emit('draw_response', img_data)
                # self.last_image_hash = current_image_hash
            socketio.emit('draw_response', img_data)

            render_time = time.time() - frame_start_time
            sleep_time = max(0, self.frame_interval - render_time)
            time.sleep(sleep_time)


class BaseWebViewer(ABC):
    
    def __init__(self):
        self._app = Flask(__name__)
        self._socketio = SocketIO(self._app)
        
        self._controls: List[BasicControl] = []

        self._connect_num = 0
        self._sessions = dict()
        self._shared_session: Session = None
        
        @self._app.route('/')
        def index():
            return render_template('index.html')
        
    def set_target_fps(self, fps: float):
        session = self._get_current_session()
        session.set_target_fps(fps)
    
    def get_target_fps(self) -> float:
        session = self._get_current_session()
        return session.get_target_fps()
        
    def set_fixed_resolution(
            self,
            width:                  Optional[int]  = None,
            height:                 Optional[int]  = None,
            force_fix_aspect_ratio: Optional[bool] = None
        ):
        session = self._get_current_session()
        session.set_fixed_resolution(width, height, force_fix_aspect_ratio)
        
    def set_dynamic_resolution(
            self,
            min_pixel:       Optional[int]   = None,
            max_pixel:       Optional[int]   = None,
            adjustment_step: Optional[float] = None
        ) -> None: 
        session = self._get_current_session()
        session.set_dynamic_resolution(min_pixel, max_pixel, adjustment_step)

    # def initialize(self):

        # session = Session(self._app)
        
        # for manually render
        # def _wrap_with_hook(render_func):
            # def wrapper(*args, **kwargs):
                # image = render_func(*args, **kwargs)  
                # if image is None:
                    # return
                
                # if not isinstance(image, np.ndarray):
                    # raise TypeError("Image must be a numpy array")
                
                # if len(image.shape) != 3 and len(image.shape) != 2:
                    # raise ValueError("Image must have 3 dimensions(H, W, 3/4) or 2 dimensions(H, W)")

                # current_image_height = image.shape[0]
                # current_image_width = image.shape[1]
                # if parameters.force_fix_aspect_ratio:
                    
                    # scale = max(
                        # current_image_height,
                        # current_image_width / parameters.aspect_ratio,
                    # )
                    
                    # padding_x = max(0, int((scale * parameters.aspect_ratio - current_image_width) / 2))
                    # padding_y = max(0, int((scale * 1 - current_image_height) / 2))
                # else:
                    # padding_x = 0
                    # padding_y = 0
                
                # parameters.padding_x = padding_x
                # parameters.padding_y = padding_y
                # parameters.manually_image_height = image.shape[0]
                # parameters.manually_image_width = image.shape[1]

                # if padding_x > 0 or padding_y > 0:
                    # image = np.pad(image, ((padding_y, padding_y), (padding_x, padding_x), (0, 0)), 'constant', constant_values=0)
                
                # _, buf = cv2.imencode('.jpg', image)
                # img_data = buf.tobytes()
                # parameters.socketio.emit('draw_response', img_data)

            # return wrapper

        # if hasattr(self, 'manually_render'):
            # original_method = getattr(self, 'manually_render')
            # setattr(self, 'manually_render', _wrap_with_hook(original_method))
            
        # return parameters
        
        
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
    
    
    def render(self, image_width: int, image_height: int, **kwargs) -> np.ndarray:
        raise NotImplementedError("Subclasses must implement this method")  
    
    def manully_render(self):
        return None
    
    def get_connect_num(self):
        return self._connect_num

    def run(self,
            host:            str  = '0.0.0.0',
            port:            int  = 5001,
            shared_session:  bool = False,
            manually_render: bool = False,
        ):
        for control in self._controls:
            control.set_socketio(self._socketio)

        self._init_routes(shared_session)

        self._socketio.run(self._app, debug=False, host=host, port=port)
        

    # Controls
    def add_control(self, control: BasicControl) -> None:
        if not isinstance(control, BasicControl):
            raise TypeError('control must be a subclass of BasicControl')
        
        self._controls.append(control)

    def add_button(self, 
                   text:     str,
                   callback: Callable[[dict], None],
                   ) -> None:
        
        control = Button(text, callback)
        
        self.add_control(control)
        
        return control
    
    def add_slider(self,
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
        
        self.add_control(control)
        
        return control

    def add_text(self, 
                 text: str,
                 ) -> None:
        
        control = Text(text)
        
        self.add_control(control)
        
        return control
        

    def add_dropdown(self,
                     text:        str,
                     init_option: str,
                     options:     List[str],
                     callback:    Callable[[dict], None],
                     ) -> None:
        
        control = Dropdown(text, init_option, options, callback)

        self.add_control(control)
        
        return control
    
    def add_divider(self) -> None:
        
        control = Divider()

        self.add_control(control)

        return control
        
    def add_checkbox(self,
                     text:       str,
                     init_value: bool,
                     callback:   Callable[[dict], None],
                     ) -> None:

        control = Checkbox(text, init_value, callback)

        self.add_control(control)
        
        return control
    
    def add_accordion(self,
                      text: str,
                      controls: Optional[List[BasicControl]] = None
    ) -> None:
        control = Accordion(text, controls)

        self.add_control(control)

        return control

    def add_tab(self) -> None:
        control = Tab()

        self.add_control(control)

        return control
    
    def add_inputbox(self,
                     label:    str,
                     content:  str,
                     desc:     str,
                     callback: Callable[[dict], None],
                     ):
        control = Inputbox(label, content, desc, callback)
        
        self.add_control(control)
        
        return control
    
    def add_image(self,
                  image:    np.ndarray,
                  callback: Callable[[dict], None] = None):

        control = Image(image, callback)
        
        self.add_control(control)
        
        return control

    def _get_current_session(self):
        if self._shared_session is not None:
            return self._shared_session
        else:
            return self._sessions[request.sid]

    def _init_routes(self, shared_session: bool):
        
        @self._socketio.on('connect')
        def handle_connect():

            sid = request.sid
            if shared_session:
                if self._shared_session is None:
                    self._shared_session = Session()
                
                    session = self._shared_session
                    session.controls = self._controls
                    
                    threading.Thread(target=session.start, args=(self._socketio, self.render)).start()
            else:
                session = Session()
                session.controls = [control.copy() for control in self._controls]
                
                threading.Thread(target=session.start, args=(self._socketio, self.render)).start()
                
                self._sessions[sid] = session
                
            self._connect_num += 1

        @self._socketio.on('disconnect')
        def handle_disconnect():
            sid = request.sid

            if sid in self._sessions:
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
        
        @self._socketio.on('send_canvas_size')
        def handle_send_canvas_size(data):
            session = self._get_current_session()
            
            session.canvas_width = data["canvas_width"]
            session.canvas_height = data["canvas_height"]

        @self._socketio.on('set_aspect_ratio')
        def handle_set_aspect_ratio(data):
            session = self._get_current_session()
            
            aspect_ratio = data['aspect_ratio']
            session.aspect_ratio = aspect_ratio
            
            if session.image_height is None or session.image_width is None:
                return
            
            if session.use_dynamic_resolution:
                min_pixel = min(session.image_width, session.image_height)
                if aspect_ratio > 1.0:
                    target_height = min_pixel
                    target_width = int(target_height * aspect_ratio)
                else:
                    target_width = min_pixel
                    target_height = int(target_width / aspect_ratio)
                
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

        @self._socketio.on('request_controls')
        def handle_request_controls():
            session = self._get_current_session()
            
            htmls = "\n".join([control.get_html() for control in session.controls])
            contents = []
            for control in session.controls:
                for content in control._get_content():
                    contents.append(content)
            
            emit('render_controls', {'htmls': htmls, 'contents': contents})
