from typing import Any, Callable, Optional, Dict, List, Union
from .base import BasicControl


class Container(BasicControl):
    
    TYPE = "container"
    
    def __init__(self,
                 direction: str = "vertical",  # "vertical" 或 "horizontal"
                 gap: str = "10px",
                 padding: str = "15px",
                 callback: Optional[Callable[['Container'], None]] = None,
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.direction = direction
        self.gap = gap
        self.padding = padding
        # 添加嵌套控件支持
        self.nested_controls_names = []
        self.nested_controls = {}
        
        if direction not in ["vertical", "horizontal"]:
            raise ValueError("direction must be 'vertical' or 'horizontal'")
        if not isinstance(gap, str):
            raise TypeError("gap must be a string")
        if not isinstance(padding, str):
            raise TypeError("padding must be a string")
        
    def get_html(self) -> str:
        # 根据方向设置CSS类
        direction_class = "container-vertical" if self.direction == "vertical" else "container-horizontal"
        
        container_html = f'''
        <div class="control-group">
            <div id="{self._id}" class="control-container {direction_class}" style="--gap: {self.gap}; --padding: {self.padding}; gap: {self.gap}; padding: {self.padding};">
        '''
        
        # 添加所有子控件的HTML
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            container_html += control.get_html()
        
        container_html += '''
            </div>
        </div>
        '''
        return container_html

    def get_content(self) -> Optional[Dict]:
        return None
    
    def copy(self):
        new_control = super().copy()

        for control_name in new_control.nested_controls_names:
            new_control.nested_controls[control_name] = new_control.nested_controls[control_name].copy()

        return new_control
    
    def _get_content(self) -> List[Dict]:
        basic_content = {
            "id":       self._id,
            "type":     self._type,
            "direction": self.direction,
            "gap": self.gap,
            "padding": self.padding,
            "control_count": len(self.nested_controls),
        }
        
        contents = []
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            for content in control._get_content():
                contents.append(content)
        
        return [basic_content, *contents]

    def update(self,
               direction: Optional[str] = None,
               gap: Optional[str] = None,
               padding: Optional[str] = None,
              ) -> None: 
        
        if direction is not None:
            if direction not in ["vertical", "horizontal"]:
                raise ValueError("direction must be 'vertical' or 'horizontal'")
            self.direction = direction
        
        if gap is not None:
            if not isinstance(gap, str):
                raise TypeError("gap must be a string")
            self.gap = gap
        
        if padding is not None:
            if not isinstance(padding, str):
                raise TypeError("padding must be a string")
            self.padding = padding
    
    def add_control(self, name: str, control: BasicControl) -> 'Container':
        """添加控件到容器（带名称）"""
        if not isinstance(control, BasicControl):
            raise TypeError("control must be a subclass of BasicControl")
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        
        self.nested_controls_names.append(name)
        self.nested_controls[name] = control
    
    def get_control(self, name: str) -> BasicControl:
        """获取指定名称的控件"""
        return self.nested_controls[name]
    
    def add_button(self, 
                   name:      str,
                   text:      str,
                   callback:  Optional[Callable] = None) -> 'Container':
        """添加按钮控件"""
        from .button import Button
        button = Button(text, callback)
        self.add_control(name, button)
        return self
    
    def add_slider(self,
                   name:       str,
                   text:       str,
                   callback:   Optional[Callable] = None,
                   init_value: Union[int, float] = 50,
                   min_value:  Union[int, float] = 0,
                   max_value:  Union[int, float] = 100,
                   step:       Union[int, float] = 1) -> 'Container':
        """添加滑块控件"""
        from .slider import Slider
        slider = Slider(text, callback, init_value, min_value, max_value, step)
        self.add_control(name, slider)
        return self
    
    def add_text(self, 
                 name: str,
                 text: str) -> 'Container':
        """添加文本控件"""
        from .text import Text
        text_control = Text(text)
        self.add_control(name, text_control)
        return self
    
    def add_checkbox(self,
                     name:       str,
                     text:       str,
                     init_value: bool = False,
                     callback:   Optional[Callable] = None) -> 'Container':
        """添加复选框控件"""
        from .checkbox import Checkbox
        checkbox = Checkbox(text, init_value, callback)
        self.add_control(name, checkbox)
        return self
    
    def add_dropdown(self,
                     name:        str,
                     text:        str,
                     init_option: str,
                     options:     List[str],
                     callback:    Optional[Callable] = None) -> 'Container':
        """添加下拉框控件"""
        from .dropdown import Dropdown
        dropdown = Dropdown(text, init_option, options, callback)
        self.add_control(name, dropdown)
        return self
    
    def add_inputbox(self,
                     name:     str,
                     label:    str,
                     content:  str = "",
                     desc:     str = "",
                     callback: Optional[Callable] = None) -> 'Container':
        """添加输入框控件"""
        from .inputbox import Inputbox
        inputbox = Inputbox(label, content, desc, callback)
        self.add_control(name, inputbox)
        return self
    
    def add_progress(self,
                     name:       str,
                     text:       str,
                     callback:   Optional[Callable] = None,
                     init_value: Union[int, float] = 0,
                     min_value:  Union[int, float] = 0,
                     max_value:  Union[int, float] = 100,
                     step:       Union[int, float] = 1) -> 'Container':
        """添加进度条控件"""
        from .progress import Progress
        progress = Progress(text, init_value, min_value, max_value, callback)
        self.add_control(name, progress)
        return self
    
    def add_colorpicker(self,
                        name:       str,
                        text:       str,
                        callback:   Optional[Callable] = None,
                        init_color: str = "#000000") -> 'Container':
        """添加颜色选择器控件"""
        from .colorpicker import ColorPicker
        colorpicker = ColorPicker(text, init_color, callback)
        self.add_control(name, colorpicker)
        return self
    
    def add_divider(self, name: str) -> 'Container':
        """添加分割线控件"""
        from .divider import Divider
        divider = Divider()
        self.add_control(name, divider)
        return self
    
    def set_direction(self, direction: str) -> 'Container':
        """设置排列方向"""
        if direction not in ["vertical", "horizontal"]:
            raise ValueError("direction must be 'vertical' or 'horizontal'")
        self.direction = direction
        return self
    
    def set_gap(self, gap: str) -> 'Container':
        """设置控件间距"""
        self.gap = gap
        return self
    
    def set_padding(self, padding: str) -> 'Container':
        """设置内边距"""
        self.padding = padding
        return self
    
    def clear(self) -> 'Container':
        """清空所有控件"""
        self.nested_controls_names.clear()
        self.nested_controls.clear()
        return self
    
    def get_control_count(self) -> int:
        """获取控件数量"""
        return len(self.nested_controls)
    
    def set_socketio(self, socketio, sid: str) -> None:
        """设置SocketIO，并传递给所有子控件"""
        super().set_socketio(socketio, sid)
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            control.set_socketio(socketio, sid)
    
    def _get_content(self) -> List[Dict]:
        """获取所有内容，包括子控件"""
        basic_content = {
            "id": self._id,
            "type": self._type,
            "direction": self.direction,
            "gap": self.gap,
            "padding": self.padding,
            "control_count": len(self.nested_controls),
        }
        
        contents = []
        # 添加所有子控件的内容
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            for content in control._get_content():
                contents.append(content)
        
        # 返回格式：[basic_content, *contents] - 与accordion和tab保持一致
        return [basic_content, *contents] 