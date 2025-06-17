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
        checkbox_html = '''
        <style>
        .checkbox-container {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .checkbox-container:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .control-checkbox {
            appearance: none;
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            position: relative;
            transition: all 0.3s ease;
            margin-right: 12px;
        }
        
        .control-checkbox:checked {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
        }
        
        .control-checkbox:checked::after {
            content: '✓';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        .control-checkbox:hover {
            border-color: #cbd5e0;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .control-checkbox:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .checkbox-label {
            font-weight: 500;
            color: #2d3748;
            font-size: 14px;
            cursor: pointer;
            user-select: none;
        }
        </style>
        '''
        checkbox_html += f'''
        <div class="checkbox-container">
            <input type="checkbox" id="{self._id}" class="control-checkbox" {'checked' if self.checked else ''}>
            <label for="{self._id}" class="checkbox-label">{self.text}</label>
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