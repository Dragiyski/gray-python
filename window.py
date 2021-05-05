from dragiyski.ui import OpenGLWindow
from threading import Thread, Event
from OpenGL.GL import *


class GLWindow(OpenGLWindow):
    def __init__(self, /, *args, **kwargs):
        self._gl_thread = Thread(target=self.__paint)
        self._gl_release_flag = False
        self._gl_resize_flag = True
        self._gl_passive_repaint = Event()
        super().__init__(*args, **kwargs)
        self.add_event_listener('exposed', self.__once_exposed)

    def __once_exposed(self, /, *args):
        self.remove_event_listener('exposed', self.__once_exposed)
        self.add_event_listener('size_changed', self.__on_size_changed)
        self.add_event_listener('close', self.__once_close)
        self._gl_thread.start()

    def __once_close(self, /, *args):
        self.remove_event_listener('size_changed', self.__on_size_changed)
        self.remove_event_listener('close', self.__once_exposed)
        self._gl_release_flag = True
        if isinstance(self._gl_passive_repaint, Event):
            self._gl_passive_repaint.set()
        if self._gl_thread.is_alive():
            self._gl_thread.join()

    def __on_size_changed(self, /, window, width, height):
        self._gl_resize_flag = True
        if isinstance(self._gl_passive_repaint, Event):
            self._gl_passive_repaint.set()

    def __paint(self):
        self.bindContext()
        GLWindow.setSwapInterval(1)

        self.gl_initialize()

        while not self._gl_release_flag:
            if self._gl_resize_flag:
                self.gl_resize()
                self._gl_resize_flag = False
            self.gl_paint()
            # swap() will take appropriate amount of time based on the vsync
            self.swap()
            # In passive mode, we pause this thread until repaint is required.
            # For active mode, set _gl_passive_repaint to None, this will run the loop continuously.
            if isinstance(self._gl_passive_repaint, Event):
                self._gl_passive_repaint.clear()
                self._gl_passive_repaint.wait()

        self.gl_release()
        self.releaseContext()

    def gl_initialize(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def gl_resize(self):
        width, height = self.getDrawableSize()
        glViewport(0, 0, width, height)

    def gl_paint(self):
        glClear(GL_COLOR_BUFFER_BIT)

    def gl_release(self):
        pass


if __name__ == '__main__':
    import sys

    def main():
        GLWindow.create(
            title='Raytrace',
            context_version_major=4,
            context_version_minor=6,
            profile_mask=GLWindow.ProfileMask.CORE
        )

    sys.exit(main())
