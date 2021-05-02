from sdl2 import *
from ._error import UIError

def EnsureSubsystem(flag):
    if not SDL_WasInit(flag):
        if SDL_InitSubSystem(flag) < 0:
            raise UIError

def GetNumberVideoDisplays():
    EnsureSubsystem(SDL_INIT_VIDEO)
    result = SDL_GetNumVideoDisplays()
    if result < 0:
        raise UIError
    return result

def GetDisplayName(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    result = SDL_GetDisplayName(index)
    if result is None:
        raise UIError
    return result.decode('utf-8')

def GetCurrentDisplayMode(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    mode = SDL_DisplayMode()
    if SDL_GetCurrentDisplayMode(index, mode) < 0:
        raise UIError
    return mode

def GetDesktopDisplayMode(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    mode = SDL_DisplayMode()
    if SDL_GetDesktopDisplayMode(index, mode) < 0:
        raise UIError
    return mode

def GetDisplayBounds(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    bounds = SDL_Rect()
    if SDL_GetDisplayBounds(index, bounds) < 0:
        raise UIError
    return bounds

def GetDisplayUsableBounds(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    bounds = SDL_Rect()
    if SDL_GetDisplayUsableBounds(index, bounds) < 0:
        raise UIError
    return bounds

def GetDisplayDPI(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    ddpi = SDL_GetDisplayDPI.argtypes[1]._type_()
    hdpi = SDL_GetDisplayDPI.argtypes[2]._type_()
    vdpi = SDL_GetDisplayDPI.argtypes[3]._type_()
    if SDL_GetDisplayDPI(index, ddpi, hdpi, vdpi) < 0:
        raise UIError
    return {
        'diagonal': ddpi,
        'horizontal': hdpi,
        'vertical': vdpi
    }

def GetDisplayModes(index):
    EnsureSubsystem(SDL_INIT_VIDEO)
    mode_count = SDL_GetNumDisplayModes(index)
    if mode_count < 0:
        raise UIError
    mode_list = [None] * mode_count
    for mode_index in range(0, mode_count):
        mode = SDL_DisplayMode()
        if SDL_GetDisplayMode(index, mode_index, mode) < 0:
            raise UIError
        mode_list[mode_index] = mode
    return mode_list

def CreateWindow(title, x, y, width, height, flags):
    EnsureSubsystem(SDL_INIT_VIDEO)
    sdl_window = SDL_CreateWindow(title, x, y, width, height, flags)
    if sdl_window is None:
        raise UIError
    try:
        sdl_window.contents
    except:
        raise UIError
    id = SDL_GetWindowID(sdl_window)
    if id == 0:
        SDL_DestroyWindow(sdl_window)
        raise UIError
    return (sdl_window, id)

def CreateContext(window):
    EnsureSubsystem(SDL_INIT_VIDEO)
    sdl_context = SDL_GL_CreateContext(window)
    if sdl_context is None:
        raise UIError
    return sdl_context

def GetWindowFromID(id):
    EnsureSubsystem(SDL_INIT_VIDEO)
    sdl_window = SDL_GetWindowFromID(id)
    if sdl_window is None:
        raise UIError
    try:
        sdl_window.contents
    except:
        return None
    return sdl_window