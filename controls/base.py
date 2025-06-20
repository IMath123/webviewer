from typing import Optional, Callable, Dict, List
import copy
import random
import string
import time
from flask_socketio import SocketIO
from abc import ABC, abstractmethod


RANDOM_ID_LENGTH = 8

def random_string(length: int) -> str:
    current = time.time()
    
    seed = current - int(current)

    random.seed(seed)
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


class BasicControl:

    def __init__(self,
                 type:     str,
                 callback: Optional[Callable] = None,
                 ) -> None:

        if not isinstance(type, str):
            raise TypeError("Type must be string.")

        self._type     = type
        self._callback = callback
        
        self._id = self._type + "_" + random_string(RANDOM_ID_LENGTH)
        
    def get_id(self):
        return self._id
    
    def get_control(self, name: str):
        raise RuntimeError(f"This control ({self._type}) does not have nested controls.")

    def copy(self):
        new_control = copy.deepcopy(self)
        new_control._id = self._type + "_" + random_string(RANDOM_ID_LENGTH)

        return new_control
     
    @abstractmethod
    def get_html(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def get_content(self) -> Optional[Dict]:
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_type(self) -> str:
        return self._type
    
    def get_callback(self) -> Optional[Callable[['BasicControl'], None]]:
        return self._callback
    
    def set_socketio(self, socketio: SocketIO, sid: str) -> None:
        raw_update_func = copy.copy(self.update)  # for avoiding the hook
        @socketio.on(self._id)
        def handle(data):
            raw_update_func(**data)
            if self._callback is not None:
                self._callback(self)
        
        def _wrap_with_hook(method):
            def wrapper(*args, **kwargs):
                method(*args, **kwargs)  
                content = self.get_content() 
                content["_callback"] = True
                if content is not None:
                    socketio.emit("update_" + self._id, content, room=sid)

            return wrapper

        def _wrap_without_callback(method):
            def wrapper(*args, **kwargs):
                method(*args, **kwargs)  
                content = self.get_content() 
                content["_callback"] = False
                if content is not None:
                    socketio.emit("update_" + self._id, content, room=sid)

            return wrapper

        if hasattr(self, 'update'):
            original_method = getattr(self, 'update')
            hooked_method = _wrap_with_hook(original_method)
            no_callback_method = _wrap_without_callback(original_method)
            setattr(self, 'update', hooked_method)
            setattr(self, 'update_without_callback', no_callback_method)

   
    def _get_content(self) -> List[Dict]:
        basic_content = {"id": self._id, "type": self._type}
        
        custom_content = self.get_content()

        if custom_content is not None:
            basic_content.update(custom_content)
        
        return [basic_content]
    
