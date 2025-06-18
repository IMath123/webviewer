from typing import List, Callable, Optional, Dict, Any
from .base import BasicControl

class ListBox(BasicControl):
    """
    多选列表控件。支持选项列表、已选项、回调。
    支持两种选中样式：高亮（highlight）和复选框（checkbox）。
    """
    TYPE = "listbox"

    def __init__(
        self,
        options: List[str],
        selected: Optional[List[int]] = None,
        callback: Optional[Callable[["ListBox"], None]] = None,
        multi: bool = True,
        select_style: str = "highlight"  # "highlight" or "checkbox"
    ) -> None:
        super().__init__(self.TYPE, callback)
        self.options = options
        self.selected = selected or []
        self.multi = multi
        self.select_style = select_style

        if not multi:
            if len(selected) > 1:
                raise ValueError("multi为False时，selected最多只能有1个")

    def get_html(self) -> str:
        items_html = ""
        for idx, opt in enumerate(self.options):
            selected_class = " selected" if idx in self.selected else ""
            if self.select_style == "checkbox":
                checked = "checked" if idx in self.selected else ""
                items_html += (
                    f'<div class="listbox-item{selected_class}" data-idx="{idx}" id="{self._id}-item-{idx}">' 
                    f'<input type="checkbox" class="listbox-checkbox" data-idx="{idx}" {checked}>'
                    f'<span class="listbox-label">{opt}</span>'
                    f'</div>'
                )
            else:
                items_html += f'<div class="listbox-item{selected_class}" data-idx="{idx}" id="{self._id}-item-{idx}">{opt}</div>'
        multi_attr = "data-multi=\"true\"" if self.multi else ""
        style_attr = f'data-select-style="{self.select_style}"'
        html = f'''
        <div class="control-group">
            <div class="control-listbox" id="{self._id}" {multi_attr} {style_attr}>
                {items_html}
            </div>
        </div>
        '''
        return html

    def get_content(self) -> Optional[Dict[str, Any]]:
        return {
            "options": self.options,
            "selected": self.selected,
            "multi": self.multi,
            "select_style": self.select_style
        }

    def update(
        self,
        options: Optional[List[str]] = None,
        selected: Optional[List[int]] = None,
        select_style: Optional[str] = None
    ) -> None:
        if options is not None:
            self.options = options
        if selected is not None:
            self.selected = selected
        if select_style is not None:
            self.select_style = select_style 