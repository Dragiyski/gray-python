from ._sdl import *
from ._event_thread import delegate_call, add_event_listener as _add_event_listener
from ._display import Display
from typing import Optional, Union
from enum import Enum
from threading import Event, Thread

_window_map = {}
_window_thread = None
_window_event = Event()
_window_event_name = {}

for name in dir(video): # pylint: disable=undefined-variable
    # pylint: disable=undefined-variable
    if name.startswith('SDL_WINDOWEVENT_') and isinstance(getattr(video, name), int):
        _window_event_name[getattr(video, name)] = name[len('SDL_WINDOWEVENT_'):].lower()

def _window_thread_function():
    while len(_window_map) > 0:
        _window_event.clear()
        _window_event.wait()

def _on_window_added():
    global _window_thread
    if _window_thread is None or not _window_thread.is_alive():
        _window_thread = Thread(target=_window_thread_function, daemon=False, name='UI Window Lifeline Thread')
        _window_thread.start()

def _on_window_removed():
    _window_event.set()
    
def _event_dispatch_function(type, id, data1, data2):
    # pylint: disable=unused-argument
    # First, we can retrieve Window() class object by calling it with the ID, which would either get it from the
    # _window_map or it will make new instance if this is the first time we have a window with this ID.
    # Next we must get the time of the event using _window_event_name dictionary (or convert type to string if not found)
    # Next we must dispatch the event to the Window instance itself, where the listeners added will be called.
    try:
        window = Window(id)
    except Window.NotFound:
        return
    if type == SDL_WINDOWEVENT_CLOSE:
        SDL_DestroyWindow(window)
        del _window_map[id]
        _on_window_removed()


_add_event_listener('window', _event_dispatch_function)

class WindowPosition:
    def __init__(
            self,
            x: Optional[int] = None,
            y: Optional[int] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            display: Optional[int] = None,
            x_center: bool = True,
            y_center: bool = True
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.display = display
        self.x_center = x_center
        self.y_center = y_center


def _window_position_calculate(position: WindowPosition):
    result = [None] * 4
    # Screen info has minor form of race condition!
    # Monitor can be connected and disconnected at any time.
    # When disconnected, functions calling with that index will fail (with UIError).
    # However, we cannot catch this easily, even if there is an event in the event queue, monitor would stop responding
    # to display* calls before the event is processed. But this will only affect window creation right at the time a
    # monitor is attached/detached.
    if position.display is not None:
        selected_display = Display[position.display % len(Display)]
    else:
        selected_display = None
        selected_cap = -1
        for display in Display:
            native_mode = display.native_mode()
            cap = native_mode.w * native_mode.h * native_mode.refresh_rate
            if cap > selected_cap:
                selected_cap = cap
                selected_display = display
    usable_bounds = selected_display.usable_bounds()
    if position.width is None:
        result[2] = usable_bounds.w // 2
    else:
        result[2] = min(usable_bounds.w, position.width)
    if position.height is None:
        result[3] = usable_bounds.h // 2
    else:
        result[3] = min(usable_bounds.h, position.height)
    if position.x is None:
        if position.display is None:
            if position.x_center:
                result[0] = SDL_WINDOWPOS_CENTERED
            else:
                result[0] = SDL_WINDOWPOS_UNDEFINED
        else:
            if position.x_center:
                result[0] = SDL_WINDOWPOS_CENTERED_DISPLAY(selected_display.index())
            else:
                result[0] = SDL_WINDOWPOS_UNDEFINED_DISPLAY(selected_display.index())
    elif position.x < 0:
        result[0] = max(0, usable_bounds.x + usable_bounds.w - result[2] + position.x)
    else:
        result[0] = max(0, min(position.x, usable_bounds.x + usable_bounds.w - result[2]))
    if position.y is None:
        if position.display is None:
            if position.y_center:
                result[1] = SDL_WINDOWPOS_CENTERED
            else:
                result[1] = SDL_WINDOWPOS_UNDEFINED
        else:
            if position.y_center:
                result[1] = SDL_WINDOWPOS_CENTERED_DISPLAY(selected_display.index())
            else:
                result[1] = SDL_WINDOWPOS_UNDEFINED_DISPLAY(selected_display.index())
    elif position.y < 0:
        result[1] = max(0, usable_bounds.y + usable_bounds.h - result[3] + position.y)
    else:
        result[1] = max(0, min(position.y, usable_bounds.y + usable_bounds.h - result[3]))
    return result


class _Window(type):
    def __call__(self, id):
        if id in _window_map:
            return _window_map[id]
        sdl_window = delegate_call(GetWindowFromID, id)
        if sdl_window is None:
            raise Window.NotFound(f'Unable to find Window with ID {id}')
        window = super().__new__(self)
        window.__init__(id, sdl_window)
        return window


class Window(metaclass=_Window):
    class NotFound(UIError):
        def __init__(self, message):
            # pylint: disable=bad-super-call
            super(Exception, self).__init__(message)
            
    class FullScreen(Enum):
        WINDOWED = 0
        SIMULATED = 1
        ACTUAL = 2

    def __init__(self, id: int, window: SDL_CreateWindow.restype):
        self.__id = id
        self._as_parameter_ = self.__window = window
        if id not in _window_map:
            _window_map[id] = self
            _on_window_added()

    @classmethod
    def create(
        cls,
        title: Union[str, bytes] = "",
        position: WindowPosition = WindowPosition(),
        visible: bool = True,
        resizable: bool = True,
        minimized: bool = False,
        maximized: bool = False,
        fullscreen: FullScreen = FullScreen.WINDOWED
    ):
        if isinstance(title, str):
            title = title.encode('utf-8')
        args = [title, *_window_position_calculate(position), 0]
        if visible:
            args[5] = SDL_WINDOW_SHOWN
        else:
            args[5] = SDL_WINDOW_HIDDEN
        if resizable:
            args[5] |= SDL_WINDOW_RESIZABLE
        if minimized:
            args[5] |= SDL_WINDOW_MINIMIZED
        if maximized:
            args[5] |= SDL_WINDOW_MAXIMIZED
        if fullscreen == Window.FullScreen.SIMULATED:
            args[5] |= SDL_WINDOW_FULLSCREEN_DESKTOP
        elif fullscreen == Window.FullScreen.ACTUAL:
            args[5] |= SDL_WINDOW_FULLSCREEN
        return cls._create(*args)

    @classmethod
    def _create(cls, *args):
        # pylint: disable=unpacking-non-sequence
        window, id = delegate_call(CreateWindow, *args)
        if id not in _window_map:
            self = super().__new__(cls)
            cls.__init__(self, id, window)
            return self
        return _window_map[id]
    
    def id(self):
        return self.__id
