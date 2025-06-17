from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Checkbox(BasicControl):
    
    TYPE = "checkbox"
    
    def __init__(self,
                 text:     str,
                 checked:  bool,
                 callback: Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text    = text
        self.checked = checked
        
    def get_html(self) -> str:
        checkbox_html = f'''
        <div class="control-group">
            <div class="checkbox-container">
                <input type="checkbox" id="{self._id}" class="control-checkbox" {'checked' if self.checked else ''}>
                <label for="{self._id}" class="control-label">{self.text}</label>
            </div>
        </div>
        '''
        return checkbox_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text": self.text,
            "checked": 'true' if self.checked else 'false',
        }

    def update(self,
               text   : Optional[str]  = None,
               checked: Optional[bool] = None
              ) -> None: 

        if text is not None:
            if not isinstance(text, str):
                raise TypeError("'text' must be a string")

            self.text = text
        
        if checked is not None:
            if not isinstance(checked, bool):
                raise TypeError("'checked' must be a boolean")

            self.checked = checked