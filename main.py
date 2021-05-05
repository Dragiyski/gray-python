from window import GLWindow
from dragiyski.ui import Window
from OpenGL.GL import *
import OpenGL.GL

_gl_debug_source = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_SOURCE_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_SOURCE_') and not key.endswith('_KHR')}
_gl_debug_type = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_TYPE_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_TYPE_') and not key.endswith('_KHR')}
_gl_debug_severity = {int(getattr(OpenGL.GL, key)): key[len('GL_DEBUG_SEVERITY_'):].lower() for key in dir(OpenGL.GL) if key.startswith('GL_DEBUG_SEVERITY_') and not key.endswith('_KHR')}


def shader_from_file(type: int, filename: str):
    shader = glCreateShader(type)
    with open(filename, 'rb') as file:
        source = file.read()
    k = 0


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
        self.__ray_texture = glCreateTextures.argtypes[2]._type_(0)
        glCreateTextures(GL_TEXTURE_2D_ARRAY, 1, ctypes.pointer(self.__ray_texture))
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def gl_resize(self):
        width, height = self.getDrawableSize()
        glViewport(0, 0, width, height)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.__ray_texture)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA32F, width, height, 2, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAX_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

    def gl_paint(self):
        super().gl_paint()

    def gl_release(self):
        glDeleteTextures(1, ctypes.pointer(self.__ray_texture))
        super().gl_release()


if __name__ == '__main__':
    import sys

    def main():
        RaytraceWindow.create(
            title='Raytrace',
            context_version_major=4,
            context_version_minor=6,
            profile_mask=GLWindow.ProfileMask.CORE
        )

    sys.exit(main())
