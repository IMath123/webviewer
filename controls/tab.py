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
        tab_html = f'''
        <div class="control-group">
            <div class="tab-container">
                <div class="tab-header">
        '''
        
        for i, title in enumerate(self.pages.keys()):
            div_type = "tab active" if i == 0 else "tab"
            tab_html += f'<button class="{div_type}" data-page="{self._id}-page-{i}">{title}</button>'
        
        tab_html += '''
                </div>
                <div id="pages">
        '''
        
        for i, title in enumerate(self.pages.keys()):
            actived = "tab-content active" if i == 0 else "tab-content"
            tab_html += f'<div id="{self._id}-page-{i}" class="{actived}">'
            for control in self.pages[title]["controls"]:
                html = control.get_html()
                tab_html += html
            tab_html += '</div>'
            
        tab_html += '''
                </div>
            </div>
        </div>
        '''
        
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
                   callback:  Callable[[BasicControl], None],
                   ) -> None:
        
        control = Button(text, callback)
        
        self.add_control(name, control)
        
        return self
    
    def add_slider(self,
                   name:       str,
                   text:       str,
                   callback:   Callable[[BasicControl], None],
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
                     callback:    Callable[[BasicControl], None],
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
                     callback:   Callable[[BasicControl], None],
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
                     callback: Callable[[BasicControl], None],
                     ):
        control = Inputbox(label, content, desc, callback)
        
        self.add_control(name, control)
        
        return self

    def add_image(self,
                  name:     str,
                  image:    np.ndarray,
                  callback: Callable[[BasicControl], None] = None):

        control = Image(image, callback)
        
        self.add_control(name, control)
        
        return self