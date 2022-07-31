from OpenGL.GL import glClearColor, glClear, glViewport, GL_COLOR_BUFFER_BIT

class Scene:
    def on_initialize(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def on_release(self):
        pass

    def on_play(self):
        pass

    def on_stop(self):
        pass

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)

    def on_paint(self):
        glClear(GL_COLOR_BUFFER_BIT)
