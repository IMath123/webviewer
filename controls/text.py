from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Text(BasicControl):
    
    TYPE = "text"
    
    def __init__(self,
                 text: str,
                 ) -> None:

        super().__init__(self.TYPE, None)
        
        self.text = text
        
    def get_html(self) -> str:
        # 将\n转换为HTML的<br>标签
        formatted_text = self.text.replace('\n', '<br>')
        text_html = f'''
        <div class="control-group">
            <div id="{self._id}" class="control-text">{formatted_text}</div>
        </div>
        '''
        
        return text_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text": self.text.replace('\n', '<br>')
        }

    def update(self,
               text: Optional[str] = None,
              ) -> None: 

        if text is not None:
            self.text = text
            # 更新HTML内容，将\n转换为<br>标签
            self.text = self.text.replace('\n', '<br>')