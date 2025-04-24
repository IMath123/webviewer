from typing import Any, Callable, Optional, Union, Dict, List
from .base import BasicControl


class Dropdown(BasicControl):
    
    TYPE = "dropdown"
    
    def __init__(self,
                 text:        str,
                 init_option: str,
                 options:     List[str],
                 callback:    Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text    = text
        self.option  = init_option
        self.options = options
        
        if self.option not in self.options:
            raise ValueError("init_option must be in options")
        
    def get_html(self) -> str:
        dropdown_html = '''

        <style>
        .control-dropdown {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border: 1px solid #555;
            background-color: #444;
            color: white;
        }
        </style>

        '''
        dropdown_html += f'''
<div style="display: flex; align-items: center; white-space: nowrap">
  <label for="{self._id}" class="control-text" style="margin-right: 10px;">{self.text}</label>
  <select id="{self._id}" class="control-dropdown">
'''
        for option in self.options:
            dropdown_html += f'<option value="{option}">{option}</option>'
        dropdown_html += '</select></div>'
        
        return dropdown_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":    self.text,
            "option":  self.option,
            "options": self.options,
        }

    def update(self,
               text:    Optional[str]       = None,
               option:  Optional[str]       = None,
               options: Optional[List[str]] = None,
              ) -> None: 
        
        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            
            self.text = text
        
        if option is not None:
            if not isinstance(option, str):
                raise TypeError("option must be a string")
            
            self.option = option
        
        if options is not None:
            for option in self.options:
                if not isinstance(option, str):
                    raise TypeError("options must contain only strings")

            if option not in options:
                raise ValueError("option must be in options")
            
            self.options = options