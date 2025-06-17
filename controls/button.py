from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Button(BasicControl):
    
    TYPE = "button"
    
    def __init__(self,
                 text:     str,
                 callback: Optional[Callable[['Button'], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text = text
        
    def get_html(self) -> str:
        button_html = f'''
        <div class="control-group">
            <button id="{self._id}" class="control-button">{self.text}</button>
        </div>
        '''
        
        return button_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text": self.text
        }

    def update(self,
               text: Optional[str] = None,
              ) -> None: 

        if text is not None:
            self.text = text