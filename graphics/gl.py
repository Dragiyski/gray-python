from OpenGL.GL import *

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

def gl_create_shader_from_source(type: int, source: str):
    shader = glCreateShader(type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    shader_status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if not shader_status:
        log = glGetShaderInfoLog(shader)
        glDeleteShader(shader)
        raise ShaderCompileError('=SOURCE=', log)
    return shader


def gl_create_program(*shaders):
    program = glCreateProgram()
    for shader in shaders:
        glAttachShader(program, shader)
    glLinkProgram(program)
    glValidateProgram(program)
    program_status = glGetProgramiv(program, GL_LINK_STATUS)
    if not program_status:
        log = glGetProgramInfoLog(program)
        glDeleteProgram(program)
        for shader in shaders:
            glDeleteShader(shader)
        raise ProgramLinkError(log)
    return program


def gl_get_program_uniforms(program):
    uniforms = {}
    count = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
    for index in range(count):
        name = glGetActiveUniform(program, index)[0]
        uniforms[name.decode('utf-8')] = glGetUniformLocation(program, name)
    return uniforms
