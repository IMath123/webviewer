from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Text(BasicControl):
    
    TYPE = "text"
    
    def __init__(self,
                 text: str,
                 ) -> None:

        super().__init__(self.TYPE, None)
        
        self.text = text
        
    def get_html(self) -> str:
        text_html = f'''
        <div class="control-group">
            <div id="{self._id}" class="control-text">{self.text}</div>
        </div>
        '''
        
        return text_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text": self.text
        }

    def update(self,
               text: Optional[str] = None,
              ) -> None: 

        if text is not None:
            self.text = text