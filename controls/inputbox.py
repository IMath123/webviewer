from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Inputbox(BasicControl):
    
    TYPE = "inputbox"
    
    def __init__(self,
                 label:     str,
                 init_text: str,
                 desc:      Optional[str],
                 callback:  Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.label   = label
        self.content = init_text
        self.desc    = desc

    def get_html(self) -> str:
        inputbox_html = '''
        <style>
        .input-container {
            display: flex;
            align-items: center;
            white-space: nowrap;
            position: relative; /* 让打勾符号在输入框外部排列 */
        }
        
        .input-container div {
            margin-right: 15px; /* 标签和输入框之间的间距 */
            font-size: 14px;
        }

        input[type="text"] {
            padding: 2px 3px;
            font-size: 13px;
            border: 2px solid #ddd;
            flex-grow: 1; /* 使输入框占据剩余的宽度 */
            border-radius: 5px;
            outline: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            background-color: white;
            width: 100%;
        }

        input[type="text"]:focus {
            border-color: #007BFF;
            box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
            background-color: #f0f8ff;
        }

        .checkmark {
            display: none; /* 初始隐藏打勾符号 */
            font-size: 24px;
            color: green;
            margin-left: 10px; /* 让打勾符号离输入框有一点间隔 */
        }
        </style>
        
        '''

        inputbox_html += f'''
        <div class="input-container">
            <div>{self.label}</div>
            <input type="text" id="{self.get_id()}" placeholder="{self.desc}">
            <span id="{self.get_id()}-checkmark" class="checkmark">&#10003;</span>
        </div>
        '''
        
        return inputbox_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "label":   self.label,
            "desc":    self.desc,
            "content": self.content
        }

    def update(self,
               label  : Optional[str] = None,
               content: Optional[str] = None,
               desc   : Optional[str] = None
              ) -> None: 

        if label is not None:
            if not isinstance(label, str):
                raise TypeError("label must be a string")
            
            self.label = label
        
        if content is not None:
            if not isinstance(content, str):
                raise TypeError("content must be a string")

            self.content = content

        if desc is not None:
            if not isinstance(desc, str):
                raise TypeError("desc must be a string")

            self.desc = desc
            