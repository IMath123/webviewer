from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Progress(BasicControl):
    
    TYPE = "progress"
    
    def __init__(self,
                 text:        str,
                 init_value:  Union[int, float],
                 min_value:   Union[int, float] = 0,
                 max_value:   Union[int, float] = 100,
                 callback:    Optional[Callable[['Progress'], None]] = None,
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text     = text
        self.value    = init_value
        self.min_value = min_value
        self.max_value = max_value
        
        if not isinstance(init_value, (int, float)):
            raise TypeError("init_value must be a number")
        if not isinstance(min_value, (int, float)):
            raise TypeError("min_value must be a number")
        if not isinstance(max_value, (int, float)):
            raise TypeError("max_value must be a number")
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        if init_value < min_value or init_value > max_value:
            raise ValueError("init_value must be between min_value and max_value")
        
    def get_html(self) -> str:
        percentage = ((self.value - self.min_value) / (self.max_value - self.min_value)) * 100
        progress_html = f'''
        <div class="control-group">
            <label class="control-label">{self.text}</label>
            <div id="{self._id}" class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {percentage}%"></div>
                </div>
                <div class="progress-text">{self.value}/{self.max_value} ({percentage:.1f}%)</div>
            </div>
        </div>
        '''
        return progress_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":      self.text,
            "value":     self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }

    def update(self,
               text:      Optional[str]                = None,
               value:     Optional[Union[int, float]]  = None,
               min_value: Optional[Union[int, float]]  = None,
               max_value: Optional[Union[int, float]]  = None,
              ) -> None: 
        
        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            self.text = text
        
        if min_value is not None:
            if not isinstance(min_value, (int, float)):
                raise TypeError("min_value must be a number")
            self.min_value = min_value
        
        if max_value is not None:
            if not isinstance(max_value, (int, float)):
                raise TypeError("max_value must be a number")
            self.max_value = max_value
        
        if value is not None:
            if not isinstance(value, (int, float)):
                raise TypeError("value must be a number")
            if value < self.min_value or value > self.max_value:
                raise ValueError("value must be between min_value and max_value")
            self.value = value 