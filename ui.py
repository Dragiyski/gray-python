import sys as _sys
import typing as _typing
import ctypes as _cytpes
import sdl2 as _sdl2
import queue as _queue
import threading as _threading


class Error(Exception):
    pass


def _make_error():
    return Error(_sdl2.SDL_GetError().decode('utf-8'))


"""
Once we create our first Window or other libSDL2 resource, we need to handle events. This will be done in a different
thread and most of the SDL_* functions (especially the ones from SDL_video.h and SDL_events.h) should not be used from
another thread, unless SDL documentation explicitly allows it. 
"""
_sdl_thread = None
_sdl_thread_ready = None
_sdl_exception = None
_sdl_queue = None
_sdl_command_event = None
_sdl_name_event = {
    256: 'SDL_QUIT',
    257: 'SDL_APP_TERMINATING',
    258: 'SDL_APP_LOWMEMORY',
    259: 'SDL_APP_WILLENTERBACKGROUND',
    260: 'SDL_APP_DIDENTERBACKGROUND',
    261: 'SDL_APP_WILLENTERFOREGROUND',
    262: 'SDL_APP_DIDENTERFOREGROUND',
    263: 'SDL_LOCALECHANGED',
    336: 'SDL_DISPLAYEVENT',
    512: 'SDL_WINDOWEVENT',
    513: 'SDL_SYSWMEVENT',
    768: 'SDL_KEYDOWN',
    769: 'SDL_KEYUP',
    770: 'SDL_TEXTEDITING',
    771: 'SDL_TEXTINPUT',
    772: 'SDL_KEYMAPCHANGED',
    1024: 'SDL_MOUSEMOTION',
    1025: 'SDL_MOUSEBUTTONDOWN',
    1026: 'SDL_MOUSEBUTTONUP',
    1027: 'SDL_MOUSEWHEEL',
    1536: 'SDL_JOYAXISMOTION',
    1537: 'SDL_JOYBALLMOTION',
    1538: 'SDL_JOYHATMOTION',
    1539: 'SDL_JOYBUTTONDOWN',
    1540: 'SDL_JOYBUTTONUP',
    1541: 'SDL_JOYDEVICEADDED',
    1542: 'SDL_JOYDEVICEREMOVED',
    1616: 'SDL_CONTROLLERAXISMOTION',
    1617: 'SDL_CONTROLLERBUTTONDOWN',
    1618: 'SDL_CONTROLLERBUTTONUP',
    1619: 'SDL_CONTROLLERDEVICEADDED',
    1620: 'SDL_CONTROLLERDEVICEREMOVED',
    1621: 'SDL_CONTROLLERDEVICEREMAPPED',
    1622: 'SDL_CONTROLLERTOUCHPADDOWN',
    1623: 'SDL_CONTROLLERTOUCHPADMOTION',
    1624: 'SDL_CONTROLLERTOUCHPADUP',
    1625: 'SDL_CONTROLLERSENSORUPDATE',
    1792: 'SDL_FINGERDOWN',
    1793: 'SDL_FINGERUP',
    1794: 'SDL_FINGERMOTION',
    2048: 'SDL_DOLLARGESTURE',
    2049: 'SDL_DOLLARRECORD',
    2050: 'SDL_MULTIGESTURE',
    2304: 'SDL_CLIPBOARDUPDATE',
    4096: 'SDL_DROPFILE',
    4097: 'SDL_DROPTEXT',
    4098: 'SDL_DROPBEGIN',
    4099: 'SDL_DROPCOMPLETE',
    4352: 'SDL_AUDIODEVICEADDED',
    4353: 'SDL_AUDIODEVICEREMOVED',
    4608: 'SDL_SENSORUPDATE',
    8192: 'SDL_RENDER_TARGETS_RESET',
    8193: 'SDL_RENDER_DEVICE_RESET'
}

_sdl_name_windowevent = {
    0: 'SDL_WINDOWEVENT_NONE',
    1: 'SDL_WINDOWEVENT_SHOWN',
    2: 'SDL_WINDOWEVENT_HIDDEN',
    3: 'SDL_WINDOWEVENT_EXPOSED',
    4: 'SDL_WINDOWEVENT_MOVED',
    5: 'SDL_WINDOWEVENT_RESIZED',
    6: 'SDL_WINDOWEVENT_SIZE_CHANGED',
    7: 'SDL_WINDOWEVENT_MINIMIZED',
    8: 'SDL_WINDOWEVENT_MAXIMIZED',
    9: 'SDL_WINDOWEVENT_RESTORED',
    10: 'SDL_WINDOWEVENT_ENTER',
    11: 'SDL_WINDOWEVENT_LEAVE',
    12: 'SDL_WINDOWEVENT_FOCUS_GAINED',
    13: 'SDL_WINDOWEVENT_FOCUS_LOST',
    14: 'SDL_WINDOWEVENT_CLOSE',
    15: 'SDL_WINDOWEVENT_TAKE_FOCUS',
    16: 'SDL_WINDOWEVENT_HIT_TEST'
}


def _sdl_get_event_name(event):
    if event.type == _sdl2.SDL_WINDOWEVENT:
        return f'SDL_WINDOWEVENT({_sdl_get_windowevent_name(event)})'
    elif event.type in _sdl_name_event:
        return _sdl_name_event[event.type]
    elif event.type < _sdl2.SDL_USEREVENT:
        return f'SDL_EVENT({event.type})'
    else:
        return f'SDL_USEREVENT({event.type})'


def _sdl_get_windowevent_name(event):
    if event.window.event in _sdl_name_windowevent:
        return _sdl_name_windowevent[event.window.event]
    else:
        return f'{event.window.event}'


def _sdl_thread_callback():
    global _sdl_thread, _sdl_thread_ready, _sdl_exception, _sdl_queue, _sdl_command_event
    try:
        _sdl_exception = None
        if not _sdl2.SDL_WasInit(_sdl2.SDL_INIT_VIDEO):
            if _sdl2.SDL_InitSubSystem(_sdl2.SDL_INIT_VIDEO) < 0:
                raise _make_error()
            _sdl_command_event = None
        if _sdl_command_event is None:
            command_event = _sdl2.SDL_RegisterEvents(1)
            if command_event == 0xFFFFFFFF:
                raise _make_error()
            _sdl_command_event = command_event
        if _sdl_queue is None:
            _sdl_queue = _queue.Queue()
        _sdl_thread_ready.set()
    except:
        _sdl_exception = _sys.exc_info()
        _sdl_thread_ready.set()
        return
    try:
        event = _sdl2.SDL_Event()
        while True:
            if _sdl2.SDL_WaitEvent(event) < 0:
                raise _make_error()
            if event.type == _sdl_command_event:
                _dispatch_command_queue()
            elif event.type == _sdl2.SDL_QUIT:
                _sdl_thread_ready = None
                break
            else:
                _sdl_handle_event(event)
                if event.type in [_sdl2.SDL_DROPTEXT, _sdl2.SDL_DROPFILE] and event.drop.file is not None:
                    # event.drop.file is dynamically allocate pointer (strdup) and it is documented that it must be freed
                    ptr_file = next(x for x in event.drop._fields_ if x[0] == 'file')[1].from_buffer(event.drop,
                                                                                                     event.drop.__class__.file.offset)
                    _sdl2.SDL_free(ptr_file)
    except:
        _sdl_exception = _sys.exc_info()


def _sdl_handle_event(event):
    print(_sdl_get_event_name(event))


def _get_task():
    try:
        return _sdl_queue.get_nowait()
    except _queue.Empty:
        return None


def _dispatch_command_queue():
    while True:
        task = _get_task()
        if task is None:
            break
        _dispatch_task(task)


def _dispatch_task(task):
    try:
        task['result'] = task['function'](*task['args'], **task['kwargs'])
    except:
        task['exception'] = _sys.exc_info()
    task['event'].set()


def _ensure_sdl_thread():
    global _sdl_thread, _sdl_queue, _sdl_thread_ready
    if _sdl_thread_ready is None:
        _sdl_thread_ready = _threading.Event()
    if _sdl_thread is None or not _sdl_thread.is_alive():
        _sdl_thread = _threading.Thread(target=_sdl_thread_callback, daemon=False, name="SDL Video Thread")
        _sdl_thread.start()
    _sdl_thread_ready.wait()
    if _sdl_exception is not None:
        raise _sdl_exception[1]


def _delegate_call(function, *args, **kwargs):
    task = {
        'function': function,
        'args': args,
        'kwargs': kwargs,
        'result': None,
        'exception': None,
        'event': _threading.Event()
    }
    _sdl_queue.put(task)
    sdl_event = _sdl2.SDL_Event()
    sdl_event.type = _sdl_command_event
    if _sdl2.SDL_PushEvent(sdl_event) < 0:
        raise _make_error()
    task['event'].wait()
    if task['exception'] is not None:
        raise task['exception'][1]
    return task['result']


class Display:
    pass


def _s_get_display_info():
    display_count = _sdl2.SDL_GetNumVideoDisplays()
    if display_count < 0:
        raise _make_error()
    display_list = [None] * display_count
    for display_index in range(0, display_count):
        display = Display()
        display.index = display_index
        display.name = _sdl2.SDL_GetDisplayName(display_index)
        if display.name is None:
            raise _make_error()
        display.name = display.name.decode('utf-8')
        display.bounds = _sdl2.SDL_Rect()
        if _sdl2.SDL_GetDisplayBounds(display_index, display.bounds) < 0:
            raise _make_error()
        display.usable_bounds = _sdl2.SDL_Rect()
        if _sdl2.SDL_GetDisplayUsableBounds(display_index, display.usable_bounds) < 0:
            raise _make_error()
        display.ddpi = _sdl2.SDL_GetDisplayDPI.argtypes[1]._type_()
        display.hdpi = _sdl2.SDL_GetDisplayDPI.argtypes[2]._type_()
        display.vdpi = _sdl2.SDL_GetDisplayDPI.argtypes[3]._type_()
        ddpi = _sdl2.SDL_GetDisplayDPI.argtypes[1](display.ddpi)
        hdpi = _sdl2.SDL_GetDisplayDPI.argtypes[2](display.hdpi)
        vdpi = _sdl2.SDL_GetDisplayDPI.argtypes[3](display.vdpi)
        if _sdl2.SDL_GetDisplayDPI(display_index, ddpi, hdpi, vdpi) < 0:
            raise _make_error()
        display.ddpi = display.ddpi.value
        display.hdpi = display.hdpi.value
        display.vdpi = display.vdpi.value
        display.native_display_mode = _sdl2.SDL_DisplayMode()
        if _sdl2.SDL_GetDesktopDisplayMode(display_index, display.native_display_mode) < 0:
            raise _make_error()
        display.current_display_mode = _sdl2.SDL_DisplayMode()
        if _sdl2.SDL_GetCurrentDisplayMode(display_index, display.current_display_mode) < 0:
            raise _make_error()
        display_mode_count = _sdl2.SDL_GetNumDisplayModes(display_index)
        if display_mode_count < 0:
            raise _make_error()
        display.display_modes = [None] * display_mode_count
        for display_mode_index in range(0, display_mode_count):
            display_mode = _sdl2.SDL_DisplayMode()
            if _sdl2.SDL_GetDisplayMode(display_index, display_mode_index, display_mode) < 0:
                raise _make_error()
            display.display_modes[display_mode_index] = display_mode
        display_list[display_index] = display
    return display_list


def _s_create_window(title, x, y, w, h, flags):
    window = _sdl2.SDL_CreateWindow(title, x, y, w, h, flags)
    if window is None:
        raise _make_error()
    return window


class WindowPosition:
    def __init__(
            self,
            x: _typing.Optional[int] = None,
            y: _typing.Optional[int] = None,
            width: _typing.Optional[int] = None,
            height: _typing.Optional[int] = None,
            display: _typing.Optional[int] = None,
            x_center: bool = True,
            y_center: bool = True
    ):
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height
        self.__display = display
        self.__x_center = x_center
        self.__y_center = y_center

    def __compute(self):
        if not hasattr(self, '_WindowPosition__computed'):
            self.__computed = {}
            display_info = _delegate_call(_s_get_display_info)
            if self.__display is not None:
                selected_display_index = self.__display % len(display_info)
                selected_display = display_info[selected_display_index]
            else:
                selected_display = None
                selected_cap = -1
                for display in display_info:
                    cap = display.native_display_mode.w * display.native_display_mode.h * display.native_display_mode.refresh_rate
                    if cap > selected_cap:
                        selected_cap = cap
                        selected_display = display
            self.__computed['display'] = selected_display
            if self.__width is None:
                self.__computed['width'] = display.usable_bounds.w // 2
            else:
                self.__computed['width'] = min(display.usable_bounds.w, self.__width)
            if self.__height is None:
                self.__computed['height'] = display.usable_bounds.h // 2
            else:
                self.__computed['height'] = min(display.usable_bounds.h, self.__height)
            if self.__x is None:
                if self.__display is None:
                    if self.__x_center:
                        self.__computed['x'] = _sdl2.SDL_WINDOWPOS_CENTERED
                    else:
                        self.__computed['x'] = _sdl2.SDL_WINDOWPOS_UNDEFINED
                else:
                    if self.__x_center:
                        self.__computed['x'] = _sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(selected_display.index)
                    else:
                        self.__computed['x'] = _sdl2.SDL_WINDOWPOS_UNDEFINED_DISPLAY(selected_display.index)
            elif self.__x < 0:
                self.__computed['x'] = max(0, display.usable_bounds.x + display.usable_bounds.w - self.__computed[
                    'width'] + self.__x)
            else:
                self.__computed['x'] = max(0, min(self.__x,
                                                  display.usable_bounds.x + display.usable_bounds.w - self.__computed[
                                                      'width']))
            if self.__y is None:
                if self.__display is None:
                    if self.__y_center:
                        self.__computed['y'] = _sdl2.SDL_WINDOWPOS_CENTERED
                    else:
                        self.__computed['y'] = _sdl2.SDL_WINDOWPOS_UNDEFINED
                else:
                    if self.__y_center:
                        self.__computed['y'] = _sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(selected_display.index)
                    else:
                        self.__computed['y'] = _sdl2.SDL_WINDOWPOS_UNDEFINED_DISPLAY(selected_display.index)
            elif self.__y < 0:
                self.__computed['y'] = max(0, display.usable_bounds.y + display.usable_bounds.h - self.__computed[
                    'height'] + self.__y)
            else:
                self.__computed['y'] = max(0, min(self.__y,
                                                  display.usable_bounds.y + display.usable_bounds.h - self.__computed[
                                                      'height']))

    def x(self):
        self.__compute()
        return self.__computed['x']

    def y(self):
        self.__compute()
        return self.__computed['y']

    def width(self):
        self.__compute()
        return self.__computed['width']

    def height(self):
        self.__compute()
        return self.__computed['height']

    def display(self):
        self.__compute()
        return self.__computed['display']

    def has_width(self):
        return self.__width is not None

    def has_height(self):
        return self.__height is not None


"""
The windows are quite peculiar resource. Their references are hold by the libSDL in special alive thread, until the last
window is closed.
"""


class Window:
    def __init__(
            self,
            title: _typing.Union[bytes, str],
            position: WindowPosition = WindowPosition(),
            resizable: bool = True,
            visible: bool = True,
            minimized: bool = False,
            maximized: bool = False,
            fullscreen: int = 0
    ):
        _ensure_sdl_thread()
        flags = _sdl2.SDL_WINDOW_SHOWN if visible else _sdl2.SDL_WINDOW_HIDDEN
        if type(title) is str:
            title = title.encode('utf-8')
        x = position.x()
        y = position.y()
        w = position.width()
        h = position.height()
        display = position.display()
        if resizable:
            flags |= _sdl2.SDL_WINDOW_RESIZABLE
        if minimized:
            flags |= _sdl2.SDL_WINDOW_MINIMIZED
        if maximized:
            flags |= _sdl2.SDL_WINDOW_MAXIMIZED
        if fullscreen == 1:
            flags |= _sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
            if not position.has_width():
                w = display.current_display_mode.w
            if not position.has_height():
                h = display.current_display_mode.h
        elif fullscreen == 2:
            flags |= _sdl2.SDL_WINDOW_FULLSCREEN
            if not position.has_width():
                w = display.native_display_mode.w
            if not position.has_height():
                h = display.native_display_mode.h
        self.__window = _delegate_call(_s_create_window, title, x, y, w, h, flags)
