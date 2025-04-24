from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Button(BasicControl):
    
    TYPE = "button"
    
    def __init__(self,
                 text:     str,
                 callback: Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text = text
        
    def get_html(self) -> str:
        button_html = '''
        <style>
        .control-button {
            background-color: #555;
            color: white;
            border: none;
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .control-button:hover {
            background-color: #666;
        }
        </style>
        '''
        button_html += f'''
        <button id="{self._id}" class="control-button">{self.text}</button>
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