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
        slider_html = '''
        <style>
        /* 滑块容器样式 */
        .slider-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            white-space: nowrap;
            background: rgba(255, 255, 255, 0.8);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        /* 第一行：标题和当前值 */
        .slider-header {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-bottom: 12px;
            align-items: center;
        }

        .slider-header span {
            font-weight: 500;
            color: #2d3748;
            font-size: 14px;
        }

        /* 当前值输入框 */
        .slider-input {
            max-width: 50px;
            min-width: 30px;
            text-align: center;
            font-size: 14px;
            padding: 6px 8px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            outline: none;
            transition: all 0.3s ease;
            background: white;
            color: #2d3748;
            font-weight: 500;
        }

        .slider-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        /* 滑块样式 */
        .slider {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 8px;
            background: linear-gradient(90deg, #e2e8f0 0%, #cbd5e0 100%);
            outline: none;
            opacity: 1;
            transition: all 0.3s ease;
            border-radius: 4px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }

        .slider:hover {
            background: linear-gradient(90deg, #cbd5e0 0%, #a0aec0 100%);
        }

        /* 滑块的圆形拖动按钮 */
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            border-radius: 50%;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            border: 2px solid white;
        }

        .slider::-webkit-slider-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
        }

        .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            border-radius: 50%;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            border: 2px solid white;
        }

        .slider::-moz-range-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
        }
        </style>

        '''
        
        slider_html += f'''

        <div class="slider-container">
            <div class="slider-header">
                <span>{self.text}</span>
                <input type="range" min="{self.min}" max="{self.max}" step="{self.step}" value="{self.value}" class="slider" id="{self._id}">
                <input type="text" id="{self._id}-slider-value-input" class="slider-input" value="{self.value}">
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