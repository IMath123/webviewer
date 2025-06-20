from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl


class Text(BasicControl):
    """
    文本显示控件。支持自动换行、最大显示行数、行号、字体颜色、对齐、字号、加粗、斜体、下划线、阴影、行高等参数。
    :param text: 显示的文本内容，支持\n换行
    :param wrap: 是否自动换行（超出宽度自动换行），默认True
    :param max_lines: 最大显示行数，None为不限制
    :param show_line_numbers: 是否显示行号，默认False
    :param color: 字体颜色（如#333、red等），默认继承主题
    :param align: 对齐方式（left/center/right）
    :param font_size: 字体大小（如'16px','1.2em'）
    :param bold: 是否加粗
    :param italic: 是否斜体
    :param underline: 是否下划线
    :param shadow: 文本阴影（如'2px 2px 4px #000'）
    :param line_height: 行高（如'1.6','24px'）
    """
    
    TYPE = "text"
    
    def __init__(self,
                 text: str,
                 wrap: bool = True,
                 max_lines: Optional[int] = None,
                 show_line_numbers: bool = False,
                 color: Optional[str] = None,
                 align: Optional[str] = None,
                 font_size: Optional[str] = None,
                 bold: bool = False,
                 italic: bool = False,
                 underline: bool = False,
                 shadow: Optional[str] = None,
                 line_height: Optional[str] = None
                 ) -> None:
        """
        Initializes a new Text instance.
        :param text: The text to be displayed.
        :param wrap: Whether to wrap the text when it exceeds the width.
        :param max_lines: The maximum number of lines to display. None means no limit.
        :param show_line_numbers: Whether to show line numbers.
        :param color: The font color.
        :param align: The text alignment.
        :param font_size: The font size.
        :param bold: Whether to make the text bold.
        :param italic: Whether to make the text italic.
        :param underline: Whether to underline the text.
        :param shadow: The text shadow.
        :param line_height: The line height.
        """
        super().__init__(self.TYPE, None)
        
        # 参数校验
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(wrap, bool):
            raise TypeError("wrap must be a boolean")
        if not isinstance(show_line_numbers, bool):
            raise TypeError("show_line_numbers must be a boolean")
        if not isinstance(bold, bool):
            raise TypeError("bold must be a boolean")
        if not isinstance(italic, bool):
            raise TypeError("italic must be a boolean")
        if not isinstance(underline, bool):
            raise TypeError("underline must be a boolean")
        
        # 验证max_lines参数
        if max_lines is not None:
            try:
                max_lines = int(max_lines)
                if max_lines <= 0:
                    raise ValueError("max_lines must be positive")
            except (TypeError, ValueError):
                raise TypeError("max_lines must be a positive integer")
        
        # 验证align参数
        if align is not None:
            if not isinstance(align, str):
                raise TypeError("align must be a string")
            if align not in ["left", "center", "right", "justify"]:
                raise ValueError("align must be one of: left, center, right, justify")
        
        self.text = text
        self.wrap = wrap
        self.max_lines = max_lines
        self.show_line_numbers = show_line_numbers
        self.color = color
        self.align = align
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.shadow = shadow
        self.line_height = line_height
        
    def get_html(self) -> str:
        """
        生成HTML，支持自动换行、最大行数、行号、字体颜色、对齐、字号、加粗、斜体、下划线、阴影、行高等。
        CSS类说明：
        - control-text：基础样式
        - control-text-nowrap：不自动换行，超出显示横向滚动条
        - control-text-linenum：显示行号
        - text-linenum：行号栏
        - text-content：内容栏
        """
        lines = self.text.split("\n")
        # 行号栏
        line_num_html = ""
        if self.show_line_numbers:
            line_num_html = '<div class="text-linenum">' + "<br>".join(str(i+1) for i in range(len(lines))) + '</div>'
        # 内容栏
        content_html = '<div class="text-content">' + "<br>".join(lines) + '</div>'
        # 样式
        classes = ["control-text"]
        if not self.wrap:
            classes.append("control-text-nowrap")
        if self.show_line_numbers:
            classes.append("control-text-linenum")
        style = []
        if self.color:
            style.append(f"color: {self.color};")
        if self.max_lines:
            style.append(f"max-height: calc({self.max_lines} * 1.6em);")
            style.append("overflow-y: auto;")
        if self.align:
            style.append(f"text-align: {self.align};")
        if self.font_size:
            style.append(f"font-size: {self.font_size};")
        if self.bold:
            style.append("font-weight: bold;")
        if self.italic:
            style.append("font-style: italic;")
        if self.underline:
            style.append("text-decoration: underline;")
        if self.shadow:
            style.append(f"text-shadow: {self.shadow};")
        if self.line_height:
            style.append(f"line-height: {self.line_height};")
        style_str = ''
        if style:
            style_str = 'style="' + ' '.join(style) + '"'
        # 拼接class属性
        class_str = ' '.join(classes)
        html = '<div class="control-group"><div id="{}" class="{}" {}>{}{}</div></div>'.format(self._id, class_str, style_str, line_num_html, content_html)
        return html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text": self.text
        }

    def update(self,
               text: Optional[str] = None,
              ) -> None: 
        """
        Updates the text content.
        :param text: The new text content.
        """
        if text is not None:
            self.text = text