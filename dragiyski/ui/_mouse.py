from ._sdl import *
from ._event_thread import delegate_call
import ctypes

class MouseState:
    def __init__(self, state, x, y):
        self.x = x
        self.y = y
        self.left_button = state & SDL_BUTTON_LMASK
        self.middle_button = state & SDL_BUTTON_MMASK
        self.right_button = state & SDL_BUTTON_RMASK
        self.x1_button = state & SDL_BUTTON_X1MASK
        self.x2_button = state & SDL_BUTTON_X2MASK

def getGlobalMouseState():
    if not SDL_WasInit(SDL_INIT_VIDEO):
        delegate_call(InitSubsystem, SDL_INIT_VIDEO)
    x = ctypes.c_int(0)
    y = ctypes.c_int(0)
    state = SDL_GetGlobalMouseState(ctypes.pointer(x), ctypes.pointer(y))
    return MouseState(state, x.value, y.value)
