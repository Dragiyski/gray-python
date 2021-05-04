from typing import Callable

class EventEmitter:
    def __init__(self):
        self.__listeners = {}
    
    def add_event_listener(self, name: str, callback: Callable):
        if name not in self.__listeners:
            self.__listeners[name] = []
        if callback not in self.__listeners[name]:
            self.__listeners[name].append(callback)
            return True
        return False
    
    def remove_event_listener(self, name: str, callback: Callable):
        if name in self.__listeners:
            try:
                self.__listeners[name].remove(callback)
            except ValueError:
                return False
            if len(self.__listeners[name]) <= 0:
                del self.__listeners[name]
            return True
        return False

    def emit_event(self, name: str, /, *args, **kwargs):
        if name in self.__listeners:
            for callback in self.__listeners[name]:
                callback(self, *args, **kwargs)

global_event_emitter = EventEmitter()
