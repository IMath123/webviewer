from typing import Any, Callable, Optional, Dict, List, Union
from .base import BasicControl


class Table(BasicControl):
    
    TYPE = "table"
    
    def __init__(self,
                 text:        str,
                 headers:     List[str],
                 data:        List[List[Any]],
                 callback:    Optional[Callable[['Table'], None]] = None,
                 sortable:    bool = False,
                 selectable:  bool = False,
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        self.text       = text
        self.headers    = headers
        self.data       = data
        self.sortable   = sortable
        self.selectable = selectable
        self.selected_rows = []
        
        if not isinstance(headers, list):
            raise TypeError("headers must be a list")
        if not isinstance(data, list):
            raise TypeError("data must be a list")
        if not all(isinstance(header, str) for header in headers):
            raise TypeError("all headers must be strings")
        if not all(isinstance(row, list) for row in data):
            raise TypeError("all data rows must be lists")
        if not all(len(row) == len(headers) for row in data):
            raise ValueError("all data rows must have the same length as headers")
        
    def get_html(self) -> str:
        # 生成表头
        header_html = ""
        for i, header in enumerate(self.headers):
            if self.sortable:
                header_html += f'<th>{header}<span class="sort-icon" data-column="{i}">⇅</span></th>'
            else:
                header_html += f'<th>{header}</th>'
        
        # 生成数据行
        rows_html = ""
        for row_idx, row in enumerate(self.data):
            row_class = f'class="table-row" data-row="{row_idx}"'
            if self.selectable:
                row_class = f'class="table-row selectable" data-row="{row_idx}"'
            
            cells_html = ""
            for cell in row:
                cells_html += f'<td>{cell}</td>'
            
            rows_html += f'<tr {row_class}>{cells_html}</tr>'
        
        table_html = f'''
        <div class="control-group">
            <label class="control-label">{self.text}</label>
            <div class="table-container">
                <table id="{self._id}" class="control-table">
                    <thead>
                        <tr>{header_html}</tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
        '''
        return table_html
    
    def get_content(self) -> Optional[Dict]:
        return {
            "text":         self.text,
            "headers":      self.headers,
            "data":         self.data,
            "sortable":     self.sortable,
            "selectable":   self.selectable,
            "selected_rows": self.selected_rows,
        }

    def update(self,
               text:         Optional[str]           = None,
               headers:      Optional[List[str]]     = None,
               data:         Optional[List[List[Any]]] = None,
               sortable:     Optional[bool]          = None,
               selectable:   Optional[bool]          = None,
               action:       Optional[str]           = None,
               column:       Optional[int]           = None,
               row:          Optional[int]           = None,
              ) -> None: 
        
        if text is not None:
            if not isinstance(text, str):
                raise TypeError("text must be a string")
            self.text = text
        
        if headers is not None:
            if not isinstance(headers, list):
                raise TypeError("headers must be a list")
            if not all(isinstance(header, str) for header in headers):
                raise TypeError("all headers must be strings")
            self.headers = headers
        
        if data is not None:
            if not isinstance(data, list):
                raise TypeError("data must be a list")
            if not all(isinstance(row, list) for row in data):
                raise TypeError("all data rows must be lists")
            if not all(len(row) == len(self.headers) for row in data):
                raise ValueError("all data rows must have the same length as headers")
            self.data = data
        
        if sortable is not None:
            if not isinstance(sortable, bool):
                raise TypeError("sortable must be a boolean")
            self.sortable = sortable
        
        if selectable is not None:
            if not isinstance(selectable, bool):
                raise TypeError("selectable must be a boolean")
            self.selectable = selectable
        
        # 处理排序事件
        if action == 'sort' and column is not None:
            print(f"Table sort event received: action={action}, column={column}")
            if self.sortable:
                print(f"Sorting table by column {column}")
                self.sort_by_column(column, ascending=True)
                print(f"Table sorted. New data: {self.data}")
            else:
                print("Table is not sortable")
        
        # 处理选择事件
        if action == 'select' and row is not None:
            print(f"Table select event received: action={action}, row={row}")
            if self.selectable:
                if row in self.selected_rows:
                    self.selected_rows.remove(row)
                else:
                    self.selected_rows.append(row)
                print(f"Selected rows: {self.selected_rows}")
            else:
                print("Table is not selectable")
    
    def add_row(self, row: List[Any]) -> None:
        """添加新行"""
        if not isinstance(row, list):
            raise TypeError("row must be a list")
        if len(row) != len(self.headers):
            raise ValueError("row must have the same length as headers")
        self.data.append(row)
    
    def remove_row(self, row_index: int) -> None:
        """删除指定行"""
        if not isinstance(row_index, int):
            raise TypeError("row_index must be an integer")
        if row_index < 0 or row_index >= len(self.data):
            raise ValueError("row_index out of range")
        self.data.pop(row_index)
    
    def sort_by_column(self, column_index: int, ascending: bool = True) -> None:
        """按列排序"""
        if not isinstance(column_index, int):
            raise TypeError("column_index must be an integer")
        if column_index < 0 or column_index >= len(self.headers):
            raise ValueError("column_index out of range")
        
        self.data.sort(key=lambda row: row[column_index], reverse=not ascending)
    
    def get_selected_rows(self) -> List[int]:
        """获取选中的行索引"""
        return self.selected_rows.copy()
    
    def set_selected_rows(self, row_indices: List[int]) -> None:
        """设置选中的行"""
        if not isinstance(row_indices, list):
            raise TypeError("row_indices must be a list")
        if not all(isinstance(idx, int) for idx in row_indices):
            raise TypeError("all row_indices must be integers")
        if not all(0 <= idx < len(self.data) for idx in row_indices):
            raise ValueError("all row_indices must be valid")
        self.selected_rows = row_indices.copy() 