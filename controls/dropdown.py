from typing import Any, Callable, Optional, Union, Dict, List
from .base import BasicControl


class Dropdown(BasicControl):
    
    TYPE = "dropdown"
    
    def __init__(self,
                 text:        str,
                 init_option: str,
                 options:     List[str],
                 callback:    Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text    = text
        self.option  = init_option
        self.options = options
        
        if self.option not in self.options:
            raise ValueError("init_option must be in options")
        
    def get_html(self) -> str:
        dropdown_html = '''
        <style>
        .dropdown-container {
            display: flex;
            flex-direction: column;
            margin-bottom: 12px;
        }
        
        .dropdown-label {
            font-weight: 500;
            color: #2d3748;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .control-dropdown {
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: 2px solid #e2e8f0;
            background: white;
            color: #2d3748;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23667eea' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 16px;
            padding-right: 40px;
        }
        
        .control-dropdown:hover {
            border-color: #cbd5e0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .control-dropdown:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .control-dropdown option {
            padding: 8px;
            background: white;
            color: #2d3748;
        }
        </style>
        '''
        dropdown_html += f'''
        <div class="dropdown-container">
            <label for="{self._id}" class="dropdown-label">{self.text}</label>
            <select id="{self._id}" class="control-dropdown">
        '''
        for option in self.options:
            dropdown_html += f'<option value="{option}">{option}</option>'
        dropdown_html += '</select></div>'
        
        return dropdown_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":    self.text,
            "option":  self.option,
            "options": self.options,
        }

    def update(self,
               text:    Optional[str]       = None,
               option:  Optional[str]       = None,
               options: Optional[List[str]] = None,
              ) -> None: 
        
        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            
            self.text = text
        
        if option is not None:
            if not isinstance(option, str):
                raise TypeError("option must be a string")
            
            self.option = option
        
        if options is not None:
            for option in self.options:
                if not isinstance(option, str):
                    raise TypeError("options must contain only strings")

            if option not in options:
                raise ValueError("option must be in options")
            
            self.options = options