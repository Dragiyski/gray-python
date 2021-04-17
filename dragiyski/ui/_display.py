from ._sdl import *
from ._event_thread import delegate_call

_display_cache = None

# TODO: We can now add_event_listener from _event_thread, which should dispatch 'display' event
# TODO: Then we need to have additional static methods on Display: add_event_listener and remove_event_listener, adn
# TODO: redirect the incoming 'display' events to it. Adding and removing displays should invalidade _display_cache
# TODO: (just set it to None, it will recover on the first attempt to access it).

def _create_display_cache():
    global _display_cache
    display_count = GetNumberVideoDisplays()
    _display_cache = [None] * display_count
    for display_index in range(0, display_count):
        _display_cache[display_index] = Display.__new__(Display)
        Display.__init__(_display_cache[display_index], display_index)
    return _display_cache


def _ensure_display_cache():
    if _display_cache is not None:
        return _display_cache
    return delegate_call(_create_display_cache)


class _Display(type):
    def __len__(self):
        return len(_ensure_display_cache())

    def __call__(self, index: int):
        cache = _ensure_display_cache()
        return cache[index]

    def __getitem__(self, key):
        if isinstance(key, int):
            cache = _ensure_display_cache()
            try:
                return cache[key]
            except IndexError as error:
                raise IndexError(f'No monitor with index {key}').with_traceback(error.__traceback__.tb_next)
        return None

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        cache = _ensure_display_cache()
        yield from cache


class Display(metaclass=_Display):
    def __init__(self, index):
        self.__index = index

    def name(self):
        return delegate_call(GetDisplayName, self.__index)
    
    def current_mode(self):
        return delegate_call(GetCurrentDisplayMode, self.__index)
    
    def native_mode(self):
        return delegate_call(GetDesktopDisplayMode, self.__index)
    
    def bounds(self):
        return delegate_call(GetDisplayBounds, self.__index)
    
    def usable_bounds(self):
        return delegate_call(GetDisplayUsableBounds, self.__index)
    
    def dpi(self):
        return delegate_call(GetDisplayDPI, self.__index)
    
    def modes(self):
        return delegate_call(GetDisplayModes, self.__index)
    
    def index(self):
        return self.__index
