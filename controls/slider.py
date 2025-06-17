from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Slider(BasicControl):
    
    TYPE = "slider"
    
    def __init__(self,
                 text:       str,
                 callback:   Optional[Callable[[Dict], None]],
                 init_value: Union[str, int, float],
                 min:        Union[int, float],
                 max:        Union[int, float],
                 step:       Union[int, float]
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text  = text
        self.value = init_value
        self.min   = min
        self.max   = max
        self.step  = step
        
        self.dtype = float if isinstance(self.value, float) or isinstance(self.min, float) or isinstance(self.max, float) or isinstance(self.step, float) else int
        
    # def get_html(self) -> str:
    #     slider_html = '''
    #     <style>
    #     .slider {
    #         width: 100%;
    #     }
    #     .control-slider {
    #         margin-bottom: 10px;
    #     }
    #     </style>
    #     '''
    #     slider_html += f'''
    #         <div style="display: flex; align-items: center; white-space: nowrap;">
    #           <div id="{self.get_id()}-value" class="control-text" style="margin-right: 20px;"> </div>
    #           <input type="range" id="{self.get_id()}" class="slider control-slider" min="{self.min}" max="{self.max}" step="{self.step}"">
    #         </div>
    #     '''
        
    #     return slider_html
    
    def get_html(self) -> str:
        slider_html = f'''
        <div class="control-group">
            <div class="slider-container">
                <div class="slider-header">
                    <span class="control-label">{self.text}</span>
                    <input type="text" id="{self._id}-slider-value-input" class="slider-input" value="{self.value}">
                </div>
                <input type="range" min="{self.min}" max="{self.max}" step="{self.step}" value="{self.value}" class="slider" id="{self._id}">
            </div>
        </div>
        '''
        
        return slider_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":  self.text,
            # "value": str(self.value),
            "value": self.value,
            "min":   self.min,
            "max":   self.max,
            "step":  self.step
        }

    def update(self,
               text : Optional[str]                    = None,
               value: Optional[Union[str, int, float]] = None,
               min  : Optional[Union[int, float]]      = None,
               max  : Optional[Union[int, float]]      = None,
               step : Optional[Union[int, float]]      = None,
               ) -> None:

        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a str.")
            
            self.text = text

        if value is not None:
            if not isinstance(value, (str, int, float)):
                raise TypeError("value must be a str or an integer or a float.")
            
            self.value = self.dtype(value)
        
        if min is not None:
            if not isinstance(min, (int, float)):
                raise TypeError("min must be an integer or a float.")

            self.min = self.dtype(min)

        if max is not None:
            if not isinstance(max, (int, float)):
                raise TypeError("max must be an integer or a float.")
            
            self.max = self.dtype(max)

        if step is not None:
            if not isinstance(step, (int, float)):
                raise TypeError("step value must be an integer or a float.")
            
            self.step = self.dtype(step)