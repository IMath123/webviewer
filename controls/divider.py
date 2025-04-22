from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Divider(BasicControl):
    
    TYPE = "divider"
    
    def __init__(self) -> None:

        super().__init__(self.TYPE, None)
        
    def get_html(self) -> str:
        divider_html = '''

        <style>
        .control-divider {
            border: 0;
            height: 1px;
            background: #555;
            margin-bottom: 10px;
        }
        </style>

        '''
        
        divider_html += '<hr class="control-divider">'

        return divider_html
    
    def get_content(self) -> Optional[Dict]:
        return None

    def update(self) -> None: 
        pass