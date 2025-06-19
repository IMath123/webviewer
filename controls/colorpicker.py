from typing import Any, Callable, Optional, Dict
from .base import BasicControl


class ColorPicker(BasicControl):
    
    TYPE = "colorpicker"
    
    def __init__(self,
                 text:        str,
                 init_color:  str = "#000000",
                 callback:    Optional[Callable[['ColorPicker'], None]] = None,
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        # 参数校验
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(init_color, str):
            raise TypeError("init_color must be a string")
        if not self._is_valid_color(init_color):
            raise ValueError("init_color must be a valid color format (hex, rgb, rgba, or named color)")
        
        self.text  = text
        self.color = init_color
        
    def _is_valid_color(self, color: str) -> bool:
        """检查颜色格式是否有效"""
        import re
        
        # 检查十六进制颜色
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        if re.match(hex_pattern, color):
            return True
        
        # 检查RGB颜色
        rgb_pattern = r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$'
        if re.match(rgb_pattern, color):
            return True
        
        # 检查RGBA颜色
        rgba_pattern = r'^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[0-9.]+\s*\)$'
        if re.match(rgba_pattern, color):
            return True
        
        # 检查命名颜色（简化版，实际应该检查CSS标准颜色名）
        named_colors = {
            'red', 'green', 'blue', 'yellow', 'black', 'white', 'gray', 'grey',
            'orange', 'purple', 'pink', 'brown', 'cyan', 'magenta', 'lime',
            'navy', 'olive', 'teal', 'silver', 'maroon', 'fuchsia', 'aqua'
        }
        if color.lower() in named_colors:
            return True
        
        return False
        
    def get_html(self) -> str:
        colorpicker_html = f'''
        <div class="control-group">
            <label for="{self._id}" class="control-label">{self.text}</label>
            <div class="colorpicker-container">
                <input type="color" id="{self._id}" class="control-colorpicker" value="{self.color}">
                <div class="color-preview" style="background-color: {self.color}"></div>
                <span class="color-value">{self.color}</span>
            </div>
        </div>
        '''
        return colorpicker_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":  self.text,
            "color": self.color,
        }

    def update(self,
               text:  Optional[str] = None,
               color: Optional[str] = None,
              ) -> None: 
        
        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            self.text = text
        
        if color is not None:
            if not isinstance(color, str):
                raise TypeError("color must be a string")
            if not self._is_valid_color(color):
                raise ValueError("color must be a valid color format")
            self.color = color 