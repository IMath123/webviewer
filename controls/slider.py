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
        slider_html = '''
        <style>
        /* 滑块容器样式 */
        .slider-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            white-space: nowrap;
        }

        /* 第一行：标题和当前值 */
        .slider-header {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-bottom: 10px;
            align-items: center;
        }

        /* 当前值输入框 */
        .slider-input {
            max-width: 40px;
            min-width: 20px;
            text-align: center;
            font-size: 16px;
            padding: 1px;
            border: 2px solid #ddd;
            border-radius: 5px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        .slider-input:focus {
            border-color: #007BFF;
        }

        /* 第二行：最小值、滑块、最大值 */
        .slider-row {
            display: flex;
            align-items: center;
            width: 100%;
        }

        /* 最小值和最大值 */
        .slider-min, .slider-max {
            font-size: 14px;
            width: 30px;
            text-align: center;
        }

        /* 滑块样式 */
        .slider {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 6px;
            background: #ddd;
            outline: none;
            opacity: 0.7;
            transition: opacity .2s;
            margin: 0 10px;
        }

        .slider:hover {
            opacity: 1;
        }

        /* 滑块的圆形拖动按钮 */
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: #007BFF;
            cursor: pointer;
            border-radius: 50%;
        }

        .slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: #007BFF;
            cursor: pointer;
            border-radius: 50%;
        }
        </style>

        '''
        
        slider_html += f'''

        <div class="slider-container">
            <div class="slider-header">
                <span>{self.text}</span>
                <input type="range" min="{self.min}" max="{self.max}" step="{self.step}" value="{self.value}" class="slider" id="{self.get_id()}">
                <input type="text" id="{self.get_id()}-slider-value-input" class="slider-input" value="{self.value}">
            </div>
        </div> 

        '''
            # <div class="slider-row">
            #     <span class="slider-min">{self.min}</span> 
            #     <input type="range" min="{self.min}" max="{self.max}" step="{self.step}" value="{self.value}" class="slider" id="{self.get_id()}">
            #     <span class="slider-max">{self.max}</span>
            # </div>
        
        return slider_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":  self.text,
            "value": str(self.value),
            "min":   self.min,
            "max":   self.max,
            "step":  self.step
        }

    def update(self,
               value: Optional[Union[str, int, float]] = None,
               min  : Optional[Union[int, float]]      = None,
               max  : Optional[Union[int, float]]      = None,
               step : Optional[Union[int, float]]      = None,
               ) -> None:
        if value is not None:
            if not isinstance(value, (str, int, float)):
                raise TypeError("value must be a str or an integer or a float.")
            
            self.value = value
        
        if min is not None:
            if not isinstance(min, (int, float)):
                raise TypeError("min must be an integer or a float.")

            self.min = min

        if max is not None:
            if not isinstance(max, (int, float)):
                raise TypeError("max must be an integer or a float.")
            
            self.max = max

        if step is not None:
            if not isinstance(step, (int, float)):
                raise TypeError("step value must be an integer or a float.")
            
            self.step = step