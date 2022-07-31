from graphics.scene import Scene
from graphics.gl import gl_create_shader_from_source, gl_create_program, gl_get_program_uniforms
from graphics.camera import MouseCamera
from OpenGL.GL import *
from OpenGL.arrays import GLuintArray
import __main__


class SkyScene(Scene):
    def __init__(self):
        with open('shader/sky-scene.glsl', 'rb') as file:
            self.camera_source = file.read()
        self.camera = MouseCamera(field_of_view=160)

    def on_initialize(self):
        self.camera_program = gl_create_program(
            gl_create_shader_from_source(GL_COMPUTE_SHADER, self.camera_source)
        )
        self.camera_uniform = gl_get_program_uniforms(self.camera_program)
        self.screen_texture = GLuint()
        glCreateTextures(GL_TEXTURE_RECTANGLE, 1, self.screen_texture)

    def on_release(self):
        for shader in glGetAttachedShaders(self.camera_program):
            glDeleteShader(shader)
        glDeleteProgram(self.camera_program)
        self.camera_program = None
        
    def on_play(self):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, __main__.gl_framebuffer)
        glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_RECTANGLE, self.screen_texture, 0)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)
        
    def on_stop(self):
        glBindFramebuffer(GL_READ_FRAMEBUFFER, __main__.gl_framebuffer)
        glFramebufferTexture(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 0, 0)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.camera.set_screen_size(width, height)
        self.width = width
        self.height = height
        glBindTexture(GL_TEXTURE_RECTANGLE, self.screen_texture)
        glTexImage2D(GL_TEXTURE_RECTANGLE, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)

    def on_paint(self):
        glUseProgram(self.camera_program)
        glUniform2i(self.camera_uniform['screen_size'], self.camera.screen_width, self.camera.screen_height)
        glUniform2f(self.camera_uniform['view_size'], self.camera.view_width, self.camera.view_height)
        screen_center = self.camera.position + self.camera.screen_distance * self.camera.view_front
        glUniform3f(self.camera_uniform['screen_center'], *screen_center)
        glUniform3f(self.camera_uniform['camera_position'], *self.camera.position)
        glUniform3f(self.camera_uniform['camera_up'], *self.camera.view_up)
        glUniform3f(self.camera_uniform['camera_right'], *self.camera.view_right)
        glBindImageTexture(0, self.screen_texture, 0, GL_TRUE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        glDispatchCompute(self.camera.screen_width, self.camera.screen_height, 1)

        glBindFramebuffer(GL_READ_FRAMEBUFFER, __main__.gl_framebuffer)
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)
