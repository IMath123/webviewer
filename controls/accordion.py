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
                font-size: 16px;
                font-weight: 600;
                padding: 12px 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                margin-bottom: 12px;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }
            
            .accordion::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .accordion:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
            }
            
            .accordion:hover::before {
                left: 100%;
            }
            
            .arrow {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-right: 12px;
                width: 24px;
                height: 24px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 12px;
            }

            .arrow.right {
                transform: rotate(0deg);
            }

            .arrow.down {
                transform: rotate(90deg);
            }
            
            .arrow:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }

            .nested-controls {
                max-height: 0;
                overflow: hidden;
                margin-top: 0;
                margin-left: 0;
                padding: 0 20px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 0 0 12px 12px;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                opacity: 0;
                transform: translateY(-10px);
            }
            
            .nested-controls.expanded {
                max-height: 1000px;
                margin-top: 6px;
                padding: 12px 16px;
                opacity: 1;
                transform: translateY(0);
            }

            .nested-controls button {
                display: block;
                margin-bottom: 10px;
            }
        </style>
        '''

        accordion_html += f'''
            <div id={self._id} class="accordion">
                <span id="{self._id}-arrow" class="arrow {'down' if self.expanded else 'right'}">▶</span>
                {self.text}
            </div>
        '''
        
        accordion_html += f'''
            <div id="{self._id}-nestedControls" class="nested-controls {'expanded' if self.expanded else ''}">
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