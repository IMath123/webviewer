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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            margin-bottom: 8px;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
            width: 100%;
        }
        
        .control-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .control-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
        }
        
        .control-button:hover::before {
            left: 100%;
        }
        
        .control-button:active {
            transform: translateY(0);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
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