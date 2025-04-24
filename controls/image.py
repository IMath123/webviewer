import numpy as np
from typing import Any, Callable, Optional, Union, Dict
from .base import BasicControl
import cv2
import base64
import io


def image_to_data(image: np.ndarray):
    from PIL import Image
    img = Image.fromarray(image)
    
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return img_base64

def data_to_image(data: str) -> np.ndarray:
    from PIL import Image
    decoded_data = base64.b64decode(data)
    image = np.array(Image.open(io.BytesIO(decoded_data)))
    return image

class Image(BasicControl):
    
    TYPE = "image"
    
    def __init__(self,
                 init_image: np.ndarray,
                 callback: Optional[Callable[[Dict], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        if init_image is not None:
            self.image  = image_to_data(init_image)
        else:
            self.image = None
        
    def get_html(self) -> str:
        image_html = '''
        <style>
        .img-control {
            width: 100%;
            height: auto;
            margin-bottom: 20px;
        }
        </style>
        '''
        image_html += f'''
        <img class="img-control" id="{self._id}" src="" width="1" height="1">
        '''
        
        return image_html
    
    def get_content(self) -> Optional[Dict]:
        return {
                "image": self.image,
        }

    def update(self,
               image: Union[np.ndarray, str],
              ) -> None: 

        if image is not None:
            if isinstance(image, np.ndarray):
                self.image = image_to_data(image)
            elif isinstance(image, str):
                self.image = data_to_image(image)