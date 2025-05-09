from typing import Any, Callable, Optional, Union, Dict, List
from flask_socketio import SocketIO
from . import *
from collections import OrderedDict
import numpy as np
import copy


class Tab(BasicControl):
    
    TYPE = "tab"
    
    def __init__(self) -> None:

        super().__init__(self.TYPE, None)
        
        self.pages = OrderedDict()
        self.active_tab = None

    
    def copy(self):
        new_control = super().copy()

        for page_name in new_control.pages:
            for i, control in enumerate(new_control.pages[page_name]["controls"]):
                new_control.pages[page_name]["controls"][i] = control.copy()

        return new_control
    
    def add_page(self, page_name: str):
        if page_name in self.pages: return

        self.pages[page_name] = {"names": [], "controls": []}
        
        return self
    
    def add_control(self, name: str, control: BasicControl) -> None:
        if len(self.pages) == 0:
            raise ValueError("Tab must have at least one page")

        last_page_name = next(reversed(self.pages))
        self.pages[last_page_name]["names"].append(name)
        self.pages[last_page_name]["controls"].append(control)
        
    def get_html(self) -> str:
        tab_html = '''
        <style>
        /* Tab 按钮样式 */
        .tab {
            cursor: pointer;
            padding: 10px 10px;
            margin-right: 5px;
            background-color: #f1f1f1;
            border: 1px solid #ccc;
            border-radius: 10px; /* 圆角 */
            display: inline-block;
            transition: background-color 0.3s, box-shadow 0.3s; /* 动画效果 */
        }

        /* 选中状态的 tab 样式 */
        .tab.active {
            background-color: #007BFF;
            color: white;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1); /* 添加阴影 */
        }

        /* Tab 内容容器样式 */
        .tab-content {
            display: none;
            padding: 20px;
            border-radius: 10px; /* 圆角 */
            margin-top: 10px;
            background: rgba(255, 255, 255, 0.1); /* 半透明背景 */
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px); /* 毛玻璃效果：模糊 */
            border: 1px solid rgba(255, 255, 255, 0.2); /* 边框透明度 */
        }

        /* 激活状态的 tab 内容 */
        .tab-content.active {
            display: block;
        }
        </style>

        '''
        tab_html += f'<div id={self._id}>'

        for i, title in enumerate(self.pages.keys()):
            div_type = "tab active" if i == 0 else "tab"
            tab_html += f'''
                <div class="{div_type}" data-page="{self._id}-page-{i}">{title}</div>

            '''
        tab_html += '</div>\n'
        
        tab_html += '<div id="pages">\n'
        for i, title in enumerate(self.pages.keys()):
            actived = "tab-content activate" if i == 0 else "tab-content"
            tab_html += f'<div id="{self._id}-page-{i}" class="{actived}">'
            for control in self.pages[title]["controls"]:
                # control = self.pages[title]["controls"][control_name]
                html = control.get_html()
                tab_html += html
            tab_html += '</div>'
            
        tab_html += '</div>'
        
        return tab_html
    
    def get_content(self) -> Optional[Dict]:
        return None

    def update(self,
               active_tab : Optional[Union[str, int]],
              ) -> None: 

        if active_tab is not None:
            if not isinstance(active_tab, (str, int)):
                raise TypeError(f"text must be a string. Got {type(active_tab)}")
            
            if isinstance(active_tab, int):
                self.active_tab = list(self.pages.keys())[active_tab]
            else:
                self.active_tab = active_tab
        
    def set_socketio(self, socketio: SocketIO, sid: str) -> None:
        super().set_socketio(socketio, sid)

        for page_name in self.pages.keys():
            for control in self.pages[page_name]["controls"]:
                # control = self.pages[page_name]["controls"][control_name]
                control.set_socketio(socketio, sid)

    def _get_content(self) -> List[Dict]:
        if len(self.pages) == 0:
            raise ValueError("No pages found")
        
        active_tab_id = 0
        for i, page_name in enumerate(self.pages):
            if page_name == self.active_tab:
                active_tab_id = i
            
        basic_content = {
            "id":            self._id,
            "type":          self._type,
            "active_tab_id": active_tab_id
        }
        
        contents = []
        for page_name in self.pages:
            for control in self.pages[page_name]["controls"]:
                for content in control._get_content():
                    contents.append(content)
        
        return [basic_content, *contents]
    
    def add_button(self, 
                   name:      str,
                   text:      str,
                   callback:  Callable[[dict], None],
                   ) -> None:
        
        control = Button(text, callback)
        
        self.add_control(name, control)
        
        return self
    
    def add_slider(self,
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
        
        return self

    def add_text(self, 
                 name: str,
                 text: str,
                 ) -> None:
        
        control = Text(text)
        
        self.add_control(name, control)
        
        return self

    def add_dropdown(self,
                     name:        str,
                     text:        str,
                     init_option: str,
                     options:     List[str],
                     callback:    Callable[[dict], None],
                     ) -> None:
        
        control = Dropdown(text, init_option, options, callback)

        self.add_control(name, control)
        
        return self
    
    def add_divider(self, name: str) -> None:

        control = Divider()

        self.add_control(name, control)
        
        return self
        
    def add_checkbox(self,
                     name:       str,
                     text:       str,
                     init_value: bool,
                     callback:   Callable[[dict], None],
                     ) -> None:

        control = Checkbox(text, init_value, callback)

        self.add_control(name, control)
        
        return self
    
    def add_accordion(self,
                      name:     str,
                      text:     str,
                      expanded: bool = False,
                     ) -> None:
        control = Accordion(text, expanded)

        self.add_control(name, control)
        
        return self
    
    def add_tab(self, name: str):
        control = Tab()
        
        self.add_control(name, control)
        
        return self

    def add_inputbox(self,
                     name:     str,
                     label:    str,
                     content:  str,
                     desc:     str,
                     callback: Callable[[dict], None],
                     ):
        control = Inputbox(label, content, desc, callback)
        
        self.add_control(name, control)
        
        return self

    def add_image(self,
                  name:     str,
                  image:    np.ndarray,
                  callback: Callable[[dict], None] = None):

        control = Image(image, callback)
        
        self.add_control(name, control)
        
        return self