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
                 callback: Optional[Callable[['Image'], None]],
                 ) -> None:

        super().__init__(self.TYPE, callback)
        
        if init_image is not None:
            self.image  = image_to_data(init_image)
        else:
            self.image = None
        
    def get_html(self) -> str:
        image_html = f'''
        <div class="control-group">
            <img class="control-image" id="{self._id}" src="" alt="Control Image">
        </div>
        '''
        
        return image_html
    
    def get_content(self) -> Optional[Dict]:
        return {
                "image": self.image,
        }

    def update(self,
               image: Optional[Union[np.ndarray, str]] = None,
              ) -> None: 

        if image is not None:
            if isinstance(image, np.ndarray):
                self.image = image_to_data(image)
            elif isinstance(image, str):
                self.image = data_to_image(image)