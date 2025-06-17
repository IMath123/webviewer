from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Inputbox(BasicControl):
    
    TYPE = "inputbox"
    
    def __init__(self,
                 label:     str,
                 init_text: str,
                 desc:      Optional[str],
                 callback:  Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.label   = label
        self.content = init_text
        self.desc    = desc

    def get_html(self) -> str:
        inputbox_html = f'''
        <div class="control-group">
            <div class="inputbox-container">
                <label for="{self._id}" class="control-label">{self.label}</label>
                <div style="display: flex; align-items: center;">
                    <input type="text" id="{self._id}" class="control-inputbox" placeholder="{self.desc or ''}">
                    <span id="{self._id}-checkmark" class="inputbox-checkmark">✓</span>
                </div>
                {f'<div class="inputbox-desc">{self.desc}</div>' if self.desc else ''}
            </div>
        </div>
        '''
        
        return inputbox_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "label":   self.label,
            "desc":    self.desc,
            "content": self.content
        }

    def update(self,
               label  : Optional[str] = None,
               content: Optional[str] = None,
               desc   : Optional[str] = None
              ) -> None: 

        if label is not None:
            if not isinstance(label, str):
                raise TypeError("label must be a string")
            
            self.label = label
        
        if content is not None:
            if not isinstance(content, str):
                raise TypeError("content must be a string")

            self.content = content

        if desc is not None:
            if not isinstance(desc, str):
                raise TypeError("desc must be a string")

            self.desc = desc
            