from sdl2 import *
import sys
import atexit
from threading import Thread, Event, current_thread
from queue import Queue, Empty
from ._error import UIError
from typing import Optional, Callable
from traceback import print_exc

_window_event_names = {id: name for (name, id) in [(x[len('SDL_WINDOWEVENT_'):].lower(), getattr(video, x)) for x in dir(video) if x.startswith('SDL_WINDOWEVENT_')]}

def _event_thread_function():
    global _event_thread_ready, _event_thread_function, _event_thread_exception, _sdl_command_event
    _event_thread_exception = None
    try:
        if not SDL_WasInit(SDL_INIT_EVENTS):
            _sdl_command_event = None
            if SDL_InitSubSystem(SDL_INIT_EVENTS) < 0:
                raise UIError
        if _sdl_command_event is None:
            command_event = SDL_RegisterEvents(1)
            if command_event > SDL_LASTEVENT:
                raise UIError
            _sdl_command_event = command_event
        _event_thread_ready.set()
    except:
        _event_thread_exception = sys.exc_info()
        _event_thread_ready.set()
    try:
        event = SDL_Event()
        while True:
            if SDL_WaitEvent(event) < 0:
                raise UIError()
            if event.type == _sdl_command_event:
                _drain_queue()
                continue
            if event.type == SDL_QUIT:
                SDL_Quit()
                break
            _comsume_event(event)
            if event.type in [SDL_DROPFILE, SDL_DROPTEXT]:
                SDL_free(next(x for x in event.drop._fields_ if x[0] == 'file')[1].from_buffer(event.drop, event.drop.__class__.file.offset))
    except:
        _event_thread_exception = sys.exc_info()
        print_exc()
    finally:
        _event_thread_ready.clear()


_event_thread = None
_event_thread_ready = Event()
_event_thread_exception = None
_event_thread_queue = Queue(maxsize=0)
_event_thread_queue_running = False
_sdl_command_event = None


def _get_task():
    try:
        return _event_thread_queue.get_nowait()
    except Empty:
        return None


def _drain_queue():
    global _event_thread_queue_running
    _event_thread_queue_running = True
    while True:
        task = _get_task()
        if task is None:
            break
        _dispatch_task(task)
    _event_thread_queue_running = False
    # TODO: Here we can do detection whether we should quit.
    # TODO: We should quit if there is no SDL resources present (no open windows) and
    # TODO: this is the last non-daemon thread standing.
    # TODO: If the thread is created and there are non-daemon threads and no windows and the thread is created
    # TODO: we shall keep it alive, since more non-thread-safe SDL_* commands might be incoming


def _dispatch_task(task):
    try:
        task['return'] = task['function'](*task['args'], **task['kwargs'])
    except:
        task['exception'] = sys.exc_info()
    task['event'].set()


def _comsume_event(event):
    from ._window import Window
    if event.type == SDL_WINDOWEVENT:
        try:
            window = Window(event.window.windowID)
        except Window.NotFound:
            return
        window_event = _window_event_names[event.window.event]
        print(f'{window_event}: {event.window.data1, event.window.data2}')
        if event.window.event in [SDL_WINDOWEVENT_MOVED, SDL_WINDOWEVENT_RESIZED, SDL_WINDOWEVENT_SIZE_CHANGED]:
            window.emit_event(window_event, event.window.data1, event.window.data2)
        else:
            window.emit_event(window_event)
        if event.window.event == SDL_WINDOWEVENT_CLOSE:
            window._destroy()


def _ensure_event_thread():
    global _event_thread, _event_thread_exception, _event_thread_ready
    if _event_thread is None or not _event_thread.is_alive():
        _event_thread_ready.clear()
        # We shall use daemon thread here to ensure any non-window UI operations (like getting the screen information)
        # does not hold the process alive. For window operation, there should be another really light-weight non-daemon
        # thread, that is blocked most of the time, except on creation and removal of windows.
        # Therefore, the process will remain alive only if there are non-closed windows.
        _event_thread = Thread(target=_event_thread_function, daemon=True, name='UI Event Thread')
        _event_thread.start()
    _event_thread_ready.wait()
    if _event_thread_exception is not None:
        # The traceback is contained within the instance, so re-raising it here will point to the original raise in the SDL thread
        raise _event_thread_exception[1]


def delegate_call(function, /, *args, **kwargs):
    _ensure_event_thread()
    # Some functions (like event filters) will execute in the event thread, in which case if they access any interface that call
    # delegate_call() we should not add anything to any queue and block (event thread should not wait for itself)
    if current_thread() is _event_thread:
        return function(*args, **kwargs)
    task = {
        'function': function,
        'args': args,
        'kwargs': kwargs,
        'return': None,
        'exception': None,
        'event': Event()
    }
    _event_thread_queue.put(task)
    if not _event_thread_queue_running:
        event = SDL_Event()
        event.type = _sdl_command_event
        # SDL_PushEvent is thread-safe
        if SDL_PushEvent(event) < 0:
            raise UIError
    task['event'].wait()
    if task['exception'] is not None:
        raise task['exception'][1]
    return task['return']


@atexit.register
def on_process_exit():
    # Once the process exits, if there is an existing daemon event thread, we send SDL_QUIT to the message queue and
    # wait for the thread to exit. The thread will call SDL_Quit, releasing any associated SDL resources.
    global _event_thread
    if _event_thread is not None and _event_thread.is_alive():
        event = SDL_Event()
        event.type = SDL_QUIT
        if SDL_PushEvent(event) < 0:
            return
        _event_thread.join()
