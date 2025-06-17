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
            height: 2px;
            background: linear-gradient(90deg, transparent, #667eea, transparent);
            margin: 16px 0;
            border-radius: 1px;
            position: relative;
            overflow: hidden;
        }
        
        .control-divider::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        </style>
        '''
        
        divider_html += '<hr class="control-divider">'

        return divider_html
    
    def get_content(self) -> Optional[Dict]:
        return None

    def update(self) -> None: 
        pass