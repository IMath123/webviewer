from typing import Any, Callable, Optional, Union, Dict, List
from .base import BasicControl
import os


class Dropdown(BasicControl):
    
    TYPE = "dropdown"
    
    def __init__(self,
                 text:        str,
                 init_option: str,
                 options:     List[str],
                 callback:    Optional[Callable[['Dropdown'], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        # 参数校验
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(init_option, str):
            raise TypeError("init_option must be a string")
        if not isinstance(options, list):
            raise TypeError("options must be a list")
        if not options:
            raise ValueError("options cannot be empty")
        if not all(isinstance(option, str) for option in options):
            raise TypeError("all options must be strings")
        if init_option not in options:
            raise ValueError(f"init_option '{init_option}' must be one of the available options: {options}")
        
        self.text    = text
        self.option  = init_option
        self.options = options
        
    def get_html(self) -> str:
        dropdown_html = f'''
        <div class="control-group">
            <label for="{self._id}" class="control-label">{self.text}</label>
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

class ThemeDropdown(Dropdown):
    def __init__(self, init_option=None, callback=None):
        # 自动扫描 themes 目录
        themes_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'themes')
        theme_files = [f for f in os.listdir(themes_dir) if f.startswith('theme-') and f.endswith('.css')]
        options = [f[len('theme-'):-len('.css')] for f in theme_files]
        options.sort()
        if not options:
            options = ["one-dark"]  # 兜底
        if init_option is None or init_option not in options:
            init_option = options[0]
        super().__init__(
            text="主题切换",
            init_option=init_option,
            options=options,
            callback=callback
        )
        self._id = "theme_dropdown"  # 强制 id