from typing import Any, Callable, Optional, Union, Dict, List
from flask_socketio import SocketIO
from . import *
import numpy as np
import copy


class Accordion(BasicControl):
    
    TYPE = "accordion"
    
    def __init__(self,
                 text:     str,
                 expanded: bool,
                 ) -> None:

        super().__init__(self.TYPE, None)
        
        self.text     = text
        self.expanded = expanded

        self.nested_controls_names = []
        self.nested_controls = {}
    
    def copy(self):
        new_control = super().copy()

        for control_name in new_control.nested_controls_names:
            new_control.nested_controls[control_name] = new_control.nested_controls[control_name].copy()

        return new_control
    
    def add_control(self, name: str, control: BasicControl) -> None:
        self.nested_controls_names.append(name)
        self.nested_controls[name] = control
    
    def get_control(self, name: str) -> BasicControl:
        return self.nested_controls[name]
        
    def get_html(self) -> str:
        accordion_html = '''
        <style>
            .accordion {
                cursor: pointer;
                display: flex;
                align-items: center;
                font-size: 14px;
                font-weight: bold;
            }
            .arrow {
                display: inline-block;
                margin-right: 10px;
                transition: transform 0.3s ease;
            }

            .arrow.right {
                transform: rotate(0deg);
            }

            .arrow.down {
                transform: rotate(90deg);
            }

            .nested-controls {
                display: none;
                margin-top: 10px;
                margin-left: 20px;
            }

            .nested-controls button {
                display: block;
                margin-bottom: 10px;
            }
        </style>
        '''

        accordion_html += f'''
            <div id={self._id} class="accordion">
                <span id="{self._id}-arrow" class="arrow right">▶</span>
                {self.text}
            </div>

        '''
        
        accordion_html += f'''
            <div id="{self._id}-nestedControls" class="nested-controls">
        '''
        
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            html = control.get_html()
            accordion_html += html

        accordion_html += '''

            </div>
        '''
        
        return accordion_html
    
    def get_content(self) -> Optional[Dict]:
        return None

    def update(self,
               text:     Optional[str]  = None,
               expanded: Optional[bool] = None,
              ) -> None: 

        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            
            self.text = text
        
        if expanded is not None:
            if not isinstance(expanded, bool):
                raise TypeError("expanded must be a boolean")

            self.expanded = expanded


    def set_socketio(self, socketio: SocketIO, sid: str) -> None:
        super().set_socketio(socketio, sid)

        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
            control.set_socketio(socketio, sid)

    def _get_content(self) -> List[Dict]:
        basic_content = {
            "id":       self._id,
            "type":     self._type,
            "text":     self.text,
            "expanded": 'true' if self.expanded else 'false',
        }
        
        contents = []
        for control_name in self.nested_controls_names:
            control = self.nested_controls[control_name]
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