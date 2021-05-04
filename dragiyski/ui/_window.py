from ._sdl import *
from ._display import Display
from ._event_emitter import EventEmitter
from typing import Optional, Union
from enum import Enum, IntEnum, IntFlag
from threading import Event, Thread, RLock

_window_map = {}
_window_map_lock = RLock()
_window_thread = None
_window_thread_event = Event()


def _window_thread_function():
    while len(_window_map) > 0:
        _window_thread_event.clear()
        _window_thread_event.wait()


def _on_window_added():
    global _window_thread
    if _window_thread is None or not _window_thread.is_alive():
        _window_thread = Thread(target=_window_thread_function, daemon=False, name='UI Window Lifeline Thread')
        _window_thread.start()


def _on_window_removed():
    _window_thread_event.set()


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
        with _window_map_lock:
            if id in _window_map:
                return _window_map[id]
        raise Window.NotFound(f'Unable to find Window with ID {id}')


class Window(EventEmitter, metaclass=_Window):
    class NotFound(UIError):
        def __init__(self, message):
            # pylint: disable=bad-super-call
            super(Exception, self).__init__(message)

    class FullScreen(Enum):
        WINDOWED = 0
        BORDERLESS = 1
        REAL = 2

    def __init__(self, id: int, window: SDL_CreateWindow.restype):
        super().__init__()
        self.__id = id
        self._as_parameter_ = self.__window = window

    @classmethod
    def create(
        cls,
        *,
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
        if fullscreen == Window.FullScreen.BORDERLESS:
            args[5] |= SDL_WINDOW_FULLSCREEN_DESKTOP
        elif fullscreen == Window.FullScreen.REAL:
            args[5] |= SDL_WINDOW_FULLSCREEN
        return cls._create(*args)

    @classmethod
    def _create(cls, *args):
        from ._event_thread import delegate_call
        return delegate_call(cls._create_window, *args)

    def _destroy(self):
        SDL_DestroyWindow(self)
        self._as_parameter_ = self.__window = None
        with _window_map_lock:
            del _window_map[self.__id]
            _on_window_removed()

    def id(self):
        return self.__id

    @classmethod
    def _create_window(cls, *args):
        with _window_map_lock:
            window, id = CreateWindow(*args)
            self = super().__new__(cls)
            cls.__init__(self, id, window)
            _window_map[id] = self
        _on_window_added()
        return self


class OpenGLWindow(Window, metaclass=_Window):
    class ProfileMask(IntEnum):
        CORE = SDL_GL_CONTEXT_PROFILE_CORE
        COMPATIBILITY = SDL_GL_CONTEXT_PROFILE_COMPATIBILITY
        ES = SDL_GL_CONTEXT_PROFILE_ES

    class ContextFlags(IntFlag):
        DEBUG = SDL_GL_CONTEXT_DEBUG_FLAG
        FORWARD_COMPATIBLE = SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG,
        ROBUST_ACCESS = SDL_GL_CONTEXT_ROBUST_ACCESS_FLAG,
        RESET_ISOLATION = SDL_GL_CONTEXT_RESET_ISOLATION_FLAG

    @classmethod
    def create(
        cls,
        *,
        red_size: int = 8,
        green_size: int = 8,
        blue_size: int = 8,
        alpha_size: int = 0,
        double_buffer: bool = True,
        depth_size: int = 16,
        stencil_size: int = 0,
        accum_red_size: int = 0,
        accum_green_size: int = 0,
        accum_blue_size: int = 0,
        accum_alpha_size: int = 0,
        stereo: bool = False,
        multisample_buffers: int = 0,
        multisample_samples: int = 0,
        accelerated_visual: bool = True,
        context_version_major: int = 3,
        context_version_minor: int = 0,
        profile_mask: ProfileMask = ProfileMask.CORE,
        context_flags: ContextFlags = 0,
        share_with_current_context: bool = False,
        srgb_capable: bool = False,
        flush_on_release: bool = False,
        **kwargs
    ):
        from ._event_thread import delegate_call
        values = locals()
        attributes = {key: value for (key, value) in [(k, values[k]) for k in OpenGLWindow._setup_attributes.__code__.co_varnames]}
        return delegate_call(cls.__create, attributes, kwargs)

    @classmethod
    def _create(cls, *args):
        args = (*args[0:5], args[5] | SDL_WINDOW_OPENGL)
        return super(OpenGLWindow, cls)._create(*args)

    def _destroy(self):
        if self.__context is not None:
            SDL_GL_DeleteContext(self.__context)
        super()._destroy()

    @classmethod
    def __create(cls, attributes, kwargs):
        cls._setup_attributes(**attributes)
        window = super(OpenGLWindow, cls).create(**kwargs)
        try:
            window.__context = CreateContext(window)
        except:
            window._destroy()
            raise
        return window

    @staticmethod
    def _setup_attributes(
        *,
        red_size: int = 8,
        green_size: int = 8,
        blue_size: int = 8,
        alpha_size: int = 0,
        double_buffer: bool = True,
        depth_size: int = 16,
        stencil_size: int = 0,
        accum_red_size: int = 0,
        accum_green_size: int = 0,
        accum_blue_size: int = 0,
        accum_alpha_size: int = 0,
        stereo: bool = False,
        multisample_buffers: int = 0,
        multisample_samples: int = 0,
        accelerated_visual: bool = True,
        context_version_major: int = 3,
        context_version_minor: int = 0,
        profile_mask: ProfileMask = ProfileMask.CORE,
        context_flags: ContextFlags = 0,
        share_with_current_context: bool = False,
        srgb_capable: bool = False,
        flush_on_release: bool = False
    ):
        EnsureSubsystem(SDL_INIT_VIDEO)
        if SDL_GL_SetAttribute(SDL_GL_RED_SIZE, red_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, green_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, blue_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, alpha_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, int(double_buffer)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, depth_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, stencil_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ACCUM_RED_SIZE, accum_red_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ACCUM_GREEN_SIZE, accum_green_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ACCUM_BLUE_SIZE, accum_blue_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ACCUM_ALPHA_SIZE, accum_alpha_size) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_STEREO, int(stereo)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, multisample_buffers) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, multisample_samples) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, int(accelerated_visual)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, context_version_major) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, context_version_minor) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, int(profile_mask)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, int(context_flags)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_SHARE_WITH_CURRENT_CONTEXT, int(share_with_current_context)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_FRAMEBUFFER_SRGB_CAPABLE, int(srgb_capable)) < 0:
            raise UIError
        if SDL_GL_SetAttribute(SDL_GL_CONTEXT_RELEASE_BEHAVIOR, SDL_GL_CONTEXT_RELEASE_BEHAVIOR_FLUSH if flush_on_release else SDL_GL_CONTEXT_RELEASE_BEHAVIOR_NONE) < 0:
            raise UIError

    def makeCurrent(self):
        if SDL_GL_MakeCurrent(self, self.__context) < 0:
            raise UIError

    def releaseCurrent(self):
        if SDL_GL_MakeCurrent(None, None) < 0:
            raise UIError

    class SwapInterval(IntEnum):
        NONE = 0
        VSYNC = 1
        ADAPTIVE = -1

    @staticmethod
    def setSwapInterval(interval: SwapInterval):
        SetSwapInterval(int(interval))

    def swap(self):
        SDL_GL_SwapWindow(self)
