from window import GLWindow
from OpenGL.GL import *
import dragiyski.ui
import OpenGL.GL
import sdl2
import ctypes
import math
import pathlib
import os

_gl_debug_source = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_SOURCE_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_SOURCE_') and not key.endswith('_KHR')}
_gl_debug_type = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_TYPE_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_TYPE_') and not key.endswith('_KHR')}
_gl_debug_severity = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_SEVERITY_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_SEVERITY_') and not key.endswith('_KHR')}


class ShaderCompileError(Exception):
    def __init__(self, file, log):
        if isinstance(log, bytes):
            log = log.decode('utf-8')
        super().__init__(f'Failed to compile OpenGL shader: {file}\n{log}')


class ProgramLinkError(Exception):
    def __init__(self, log):
        super().__init__(f'Failed to link OpenGL program:\n{log}')


def gl_create_shader_from_file(type: int, filename: str):
    shader = glCreateShader(type)
    with open(filename, 'rb') as file:
        glShaderSource(shader, file.read())
    glCompileShader(shader)
    shader_status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if not shader_status:
        log = glGetShaderInfoLog(shader)
        glDeleteShader(shader)
        raise ShaderCompileError(filename, log)
    return shader


def gl_create_program(*shaders):
    program = glCreateProgram()
    for shader in shaders:
        glAttachShader(program, shader)
    glLinkProgram(program)
    program_status = glGetProgramiv(program, GL_LINK_STATUS)
    if not program_status:
        log = glGetProgramInfoLog(program)
        glDeleteProgram(program)
        raise ProgramLinkError(log)
    return program


def gl_get_debug_name(category: str, dictionary, value):
    if value not in dictionary:
        return f'{category}={value}'
    return dictionary[value]


def gl_debug_message_callback(
    source,
    type,
    id,
    severity,
    length,
    message,
    param
):
    # int -> PyObject* -> contents of PyObject* = py_object(<the_object>) -> py_object.value returns the actual python value
    window = ctypes.cast(param, ctypes.POINTER(ctypes.py_object)).contents.value
    print(f'[{id}][{gl_get_debug_name("source", _gl_debug_source, source)}][{gl_get_debug_name("type", _gl_debug_type, type)}][{gl_get_debug_name("severity", _gl_debug_severity, severity)}]: {message.decode("utf-8")}')


class RaytraceWindow(GLWindow):
    def gl_initialize(self):
        glEnable(GL_DEBUG_OUTPUT)
        glDebugMessageCallback(
            glDebugMessageCallback.argtypes[0](gl_debug_message_callback),
            # self -> PyObject(self) -> PyObject* -> void*
            ctypes.cast(ctypes.pointer(ctypes.py_object(self)), glDebugMessageCallback.argtypes[1])
        )
        self._ray_texture = glCreateTextures.argtypes[2]._type_(0)
        glCreateTextures(GL_TEXTURE_2D_ARRAY, 1, ctypes.pointer(self._ray_texture))
        self._raytrace_texture = glCreateTextures.argtypes[2]._type_(0)
        glCreateTextures(GL_TEXTURE_2D_ARRAY, 1, ctypes.pointer(self._raytrace_texture))
        self._screen_texture = glCreateTextures.argtypes[2]._type_(0)
        glCreateTextures(GL_TEXTURE_RECTANGLE, 1, ctypes.pointer(self._screen_texture))
        self._field_of_view = 30.0
        operation_clear_shader = gl_create_shader_from_file(GL_COMPUTE_SHADER, os.path.join(os.path.dirname(RaytraceWindow.gl_initialize.__code__.co_filename), 'shader/operation/clear.glsl'))
        self._operation_clear_program = gl_create_program(operation_clear_shader)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def gl_resize(self):
        width, height = self.getDrawableSize()
        self._width = width
        self._height = height
        glViewport(0, 0, width, height)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self._ray_texture)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA32F, width, height, 2, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAX_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self._raytrace_texture)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA32F, width, height, 4, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAX_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)
        glBindTexture(GL_TEXTURE_RECTANGLE, self._screen_texture)
        glTexImage2D(GL_TEXTURE_RECTANGLE, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)
        glBindTexture(GL_TEXTURE_RECTANGLE, 0)

    def gl_paint(self):
        super().gl_paint()
        field_of_view = self._field_of_view / 180.0 * math.pi
        min_size = min(self._width, self._height)
        view_size = [self._width / min_size, self._height / min_size]
        view_length = math.sqrt(sum([x * x for x in view_size]))
        screen_radius = view_length / math.tan(field_of_view * 0.5)

    def gl_release(self):
        glDeleteTextures(1, ctypes.pointer(self._ray_texture))
        glDeleteTextures(1, ctypes.pointer(self._raytrace_texture))
        glDeleteTextures(1, ctypes.pointer(self._screen_texture))
        for shader in glGetAttachedShaders(self._operation_clear_program):
            glDeleteShader(shader)
        glDeleteProgram(self._operation_clear_program)
        super().gl_release()


if __name__ == '__main__':
    import sys

    def main():
        # Get the current mouse position (in global coordinate system)
        state = dragiyski.ui.getGlobalMouseState()
        # Get display for those coordinates
        display = dragiyski.ui.Display.getDisplayAt(state.x, state.y)
        # Create a window at the position of the mouse coordinates. If no mouse is available and/or display is None,
        # it will create a window at the default display
        RaytraceWindow.create(
            title='Raytrace',
            context_version_major=4,
            context_version_minor=6,
            profile_mask=GLWindow.ProfileMask.CORE,
            position=dragiyski.ui.WindowPosition(display=display)
        )

    sys.exit(main())
