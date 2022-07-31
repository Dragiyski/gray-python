import threading
import ctypes
import math
from sys import exit, stderr
from traceback import print_exc
from sdl2 import *
from ui.error import UIError
from ui.display import get_display_under_cursor, get_display_bounds
from OpenGL.GL import *
from scene.sky import SkyScene
from graphics.scene import Scene

window = None
window_id = 0
gl_context = None
gl_thread = None
gl_loop_alive = True
gl_loop_running = threading.Event()
gl_need_resize = False
gl_framebuffer = None
_gl_scene_set = set()
_gl_scene_active = None
_gl_scene_next = None
_gl_scene_lock = threading.RLock()
_gl_scene_active_event = threading.Event()


def gl_main():
    global _gl_scene_next, _gl_scene_active, gl_framebuffer
    from graphics.main import on_initialize, on_paint, on_release, on_resize
    try:
        if SDL_GL_MakeCurrent(window, gl_context) < 0:
            raise UIError
        if SDL_GL_SetSwapInterval(-1) < 0:
            print('Request for variable refresh rate failed, fallback to VSync', file=stderr)
            if SDL_GL_SetSwapInterval(1) < 0:
                raise UIError
            
        gl_framebuffer = glGenFramebuffers(1)
        
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
        glHint(GL_TEXTURE_COMPRESSION_HINT, GL_NICEST)
        glHint(GL_FRAGMENT_SHADER_DERIVATIVE_HINT, GL_NICEST)

        while gl_loop_alive:
            _gl_scene_active_event.wait()
            gl_loop_running.wait()

            call_on_play = False

            with _gl_scene_lock:
                if _gl_scene_next != _gl_scene_active:
                    # A request to switch scenes is made;
                    if _gl_scene_active is not None:
                        # Notify the current scene it is stopping;
                        _gl_scene_active.on_stop()
                    _gl_scene_active = _gl_scene_next
                    # Notify the new scene that it is playing;
                    # Calling on_play() must be called after on_initialize() if the scene is new.
                    call_on_play = True
                    gl_need_resize = True

            if _gl_scene_active is not None:
                if _gl_scene_active not in _gl_scene_set:
                    _gl_scene_active.on_initialize()
                    _gl_scene_set.add(_gl_scene_active)
                    gl_need_resize = True

                if call_on_play:
                    _gl_scene_active.on_play()

                if gl_need_resize:
                    width = ctypes.c_int()
                    height = ctypes.c_int()
                    SDL_GL_GetDrawableSize(window, width, height)
                    _gl_scene_active.on_resize(width.value, height.value)
                
                _gl_scene_active.on_paint()
                
                SDL_GL_SwapWindow(window)
            else:
                # If no active scene, clear the event, so the thread is blocked.
                _gl_scene_active_event.clear()

        if _gl_scene_active is not None:
            _gl_scene_active.on_stop()

        _gl_scene_next = None

        for scene in _gl_scene_set:
            scene.on_release()
            
        glDeleteFramebuffers(1, [gl_framebuffer])

    except:
        event = SDL_Event()
        event.type = SDL_QUIT
        SDL_PushEvent(event)
        print_exc()


def main():
    global window, window_id, gl_context, gl_thread, gl_loop_alive, gl_loop_running, gl_need_resize

    # Default settings*
    # Width and Height will be maximum 1024x768, but no more than 90% of the screen.
    width = 1024
    height = 768
    title = 'Gray'

    # Step 1: Init the SDL library;
    if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0:
        raise UIError

    # Step 2: Prepare OpenGL attributes, particularly important to get OpenGL 4.6+
    SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 6)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)

    # Locate proper position for the window
    display_index = get_display_under_cursor()
    display_size = SDL_Rect()
    if SDL_GetDisplayUsableBounds(display_index, display_size) < 0:
        raise UIError

    window_position = [0] * 4
    if display_size.w * 0.9 < width:
        window_position[2] = int(display_size.w * 0.9)
    else:
        window_position[2] = width
    if window_position[3] * 0.9 < height:
        window_position[3] = int(display_size.h * 0.9)
    else:
        window_position[3] = height

    window_position[0] = display_size.x + (display_size.w - window_position[2]) // 2
    window_position[1] = display_size.y + (display_size.h - window_position[3]) // 2

    window = SDL_CreateWindow(str.encode(title, 'utf-8'), *window_position, SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE | SDL_WINDOW_INPUT_FOCUS | SDL_WINDOW_MOUSE_FOCUS)
    if window is None:
        raise UIError

    SDL_SetWindowMinimumSize(window, 160, 90)

    gl_context = SDL_GL_CreateContext(window)
    if gl_context is None:
        raise UIError
    SDL_GL_MakeCurrent(None, None)

    window_id = SDL_GetWindowID(window)
    gl_thread = threading.Thread(target=gl_main, name='DrawThread', daemon=True)
    gl_loop_running.set()
    gl_thread.start()
    set_scene(SkyScene())

    mouse_capture = False
    while True:
        event = SDL_Event()
        if SDL_WaitEvent(event) == 0:
            raise UIError
        if event.type == SDL_QUIT:
            break
        if event.type == SDL_WINDOWEVENT:
            if event.window.windowID == window_id:
                if event.window.event == SDL_WINDOWEVENT_CLOSE:
                    break
                elif event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED:
                    gl_need_resize = True
                elif event.window.event == SDL_WINDOWEVENT_FOCUS_LOST:
                    gl_loop_running.clear()
                    if SDL_SetRelativeMouseMode(0) < 0:
                        raise UIError
                    mouse_capture = False
                elif event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:
                    gl_loop_running.set()
                elif event.window.event == SDL_WINDOWEVENT_EXPOSED:
                    gl_loop_running.set()
        elif event.type == SDL_MOUSEBUTTONDOWN:
            if event.button.windowID == window_id and event.button.button == SDL_BUTTON_LEFT:
                SDL_RaiseWindow(window)
                if SDL_SetRelativeMouseMode(1) < 0:
                    raise UIError
                mouse_capture = True
        elif event.type == SDL_MOUSEBUTTONUP:
            if event.button.windowID == window_id and event.button.button == SDL_BUTTON_LEFT:
                if SDL_SetRelativeMouseMode(0) < 0:
                    raise UIError
                mouse_capture = False
        elif event.type == SDL_MOUSEMOTION:
            if event.motion.windowID == window_id and mouse_capture:
                x = ctypes.c_int()
                y = ctypes.c_int()
                w = ctypes.c_int()
                h = ctypes.c_int()
                SDL_GetWindowPosition(window, x, y)
                SDL_GetWindowSize(window, w, h)
                db = get_display_bounds()
                display = 0
                for index in range(len(db)):
                    bounds = db[index]
                    if x.value >= bounds.x and x.value < bounds.x + bounds.w and y.value <= bounds.y and y.value < bounds.y + bounds.h:
                        display = index
                        break
                bounds = db[display]
                rotation_size = min(bounds.w, bounds.h)
                delta_x = (event.motion.xrel / rotation_size) * math.pi * 2
                delta_y = (event.motion.yrel / rotation_size) * math.pi * 2
                if _gl_scene_active is not None and _gl_scene_active.camera is not None:
                    _gl_scene_active.camera.rotate(delta_x, delta_y)
                

    _join_draw_thread()
    SDL_Quit()
    return 0

def _join_draw_thread():
    global window, gl_loop_alive
    gl_loop_alive = False
    if gl_thread.is_alive():
        gl_loop_running.set()
        _gl_scene_active_event.set()
        gl_thread.join()
    if window is not None:
        SDL_DestroyWindow(window)
        window = None
        window_id = 0
        
def set_scene(scene: Scene):
    global _gl_scene_next
    with _gl_scene_lock:
        if scene != _gl_scene_active:
            _gl_scene_next = scene
            _gl_scene_active_event.set()

if __name__ == '__main__':
    exit(main())
