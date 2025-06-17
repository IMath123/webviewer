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
            flex-direction: column;
            margin-bottom: 12px;
            position: relative;
        }
        
        .input-label {
            font-weight: 500;
            color: #2d3748;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .input-wrapper {
            display: flex;
            align-items: center;
            position: relative;
        }

        input[type="text"] {
            padding: 12px 16px;
            font-size: 14px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            outline: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            background: white;
            width: 100%;
            color: #2d3748;
            font-weight: 500;
        }

        input[type="text"]:hover {
            border-color: #cbd5e0;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        input[type="text"]:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .checkmark {
            display: none;
            position: absolute;
            right: 12px;
            font-size: 18px;
            color: #10b981;
            animation: checkmarkAppear 0.3s ease;
        }
        
        @keyframes checkmarkAppear {
            0% {
                opacity: 0;
                transform: scale(0.5);
            }
            100% {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .input-desc {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
            font-style: italic;
        }
        </style>
        '''

        inputbox_html += f'''
        <div class="input-container">
            <label class="input-label">{self.label}</label>
            <div class="input-wrapper">
                <input type="text" id="{self._id}" placeholder="{self.desc}" value="{self.content}">
                <span id="{self._id}-checkmark" class="checkmark">✓</span>
            </div>
            {f'<div class="input-desc">{self.desc}</div>' if self.desc else ''}
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
            