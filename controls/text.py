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
        text_html = '''
        <style>
        .control-text {
            margin-bottom: 12px;
            padding: 8px 12px;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 8px;
            border-left: 4px solid #667eea;
            color: #2d3748;
            font-weight: 500;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        
        .control-text:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
        }
        </style>
        '''
        text_html += f'<div id="{self._id}" class="control-text">{self.text}</div>'
        
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