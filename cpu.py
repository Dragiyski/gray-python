import dragiyski.ui
import numpy
import math
import ctypes
import threading
from sdl2 import *
import renderer
        
class RenderWorker:
    def __init__(self, window):
        self.__window = window
        self.__initialized = False
        self.__resized = True
        self.__closing = False
        self.__repaint_event = threading.Event()
        self._render_thread = threading.Thread(target=self.__render)
        window.add_event_listener('exposed', self.__once_exposed)
    
    def __once_exposed(self, *args, **kwargs):
        self.__window.remove_event_listener('exposed', self.__once_exposed)
        self.__window.add_event_listener('close', self.__once_closed)
        self.__window.add_event_listener('size_changed', self.__on_size_changed)
        self.__repaint_event.set()
        self._render_thread.start()
    
    def __once_closed(self, *args, **kwargs):
        self.__window.remove_event_listener('size_changed', self.__on_size_changed)
        self.__window.remove_event_listener('close', self.__once_closed)
        if self._render_thread.is_alive():
            self.__closing = True
            self.__repaint_event.set()
            self._render_thread.join()
            
    def __on_size_changed(self, *args, **kwargs):
        self.__resized = True
        self.__repaint_event.set()
            
    def __render(self):
        if not self.__initialized:
            self.initialize()
            self.__initialized = True
        self.__repaint_event.clear()
        while not self.__closing:
            if self.__resized:
                self.resize()
                self.__resized = False
            self.render()
            self.__repaint_event.wait()
            self.__repaint_event.clear()
        self.release()
        
    def initialize(self):
        # Renderer is not thread-safe and all SDL_* calls to it must happen in the thread where it is created.
        # This thread might be different thread from the one called SDL_InitSubsystem(SDL_INIT_VIDEO),
        # but only one thread must have access to the rendering.
        self._camera_position = numpy.array([7.35889, -6.92579, 4.95831], dtype=numpy.float32)
        self._camera_direction = (0.0 - self._camera_position)
        self._camera_direction /= numpy.linalg.norm(self._camera_direction)
        self._camera_roll = 0.0
        self._screen_center = self._camera_position + self._camera_direction
        unroll_left = numpy.cross(self._camera_direction, numpy.array([0.0, 0.0, 1.0], dtype=numpy.float32))
        unroll_left /= numpy.linalg.norm(unroll_left)
        unroll_up = numpy.cross(unroll_left, self._camera_direction)
        self._camera_right = math.cos(self._camera_roll) * unroll_left + math.sin(self._camera_roll) * unroll_up
        self._camera_up = math.cos(self._camera_roll) * unroll_up - math.sin(self._camera_roll) * unroll_left
        self._field_of_view = 60.0
        
        self._cube_vertices = numpy.array([-1,1,-1,0,1,0,0,1,1,1,1,0,1,0,1,0,1,1,-1,0,1,0,1,1,1,1,1,0,0,1,1,1,-1,-1,1,0,0,1,0,0,1,-1,1,0,0,1,1,0,-1,1,1,-1,0,0,0,1,-1,-1,-1,-1,0,0,1,0,-1,-1,1,-1,0,0,0,0,1,-1,-1,0,-1,0,1,1,-1,-1,1,0,-1,0,0,0,-1,-1,-1,0,-1,0,0,1,1,1,-1,1,0,0,1,1,1,-1,1,1,0,0,0,0,1,-1,-1,1,0,0,1,0,-1,1,-1,0,0,-1,0,1,1,-1,-1,0,0,-1,1,0,-1,-1,-1,0,0,-1,0,0,-1,1,1,0,1,0,0,0,-1,1,1,0,0,1,0,1,-1,1,-1,-1,0,0,1,1,1,-1,1,0,-1,0,1,0,1,1,1,1,0,0,0,1,1,1,-1,0,0,-1,1,1], dtype=numpy.float32)
        self._cube_indices = numpy.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,0,18,1,3,19,4,6,20,7,9,21,10,12,22,13,15,23,16], dtype=numpy.uint8)
    
    def resize(self):
        surface = SDL_GetWindowSurface(self.__window)
        self._ray_texture = numpy.ndarray(shape=(2, surface.contents.h, surface.contents.w, 4), dtype=numpy.float32)
        self._raytrace_texture = numpy.ndarray(shape=(4, surface.contents.h, surface.contents.w, 4), dtype=numpy.float32)
        field_of_view = numpy.deg2rad(self._field_of_view) / 2.0
        half_diagonal = math.tan(field_of_view)
        aspect_ratio = float(surface.contents.w) / float(surface.contents.h)
        view_height = half_diagonal / math.sqrt(aspect_ratio * aspect_ratio + 1)
        view_width = aspect_ratio * view_height
        self._view_size = numpy.array([view_width, view_height], dtype=numpy.float32)
    
    def render(self):
        surface = SDL_GetWindowSurface(self.__window)
        SDL_LockSurface(surface)
        bytePointer = ctypes.cast(ctypes.c_void_p(surface.contents.pixels), ctypes.POINTER(ctypes.c_uint8))
        pixelData = numpy.ctypeslib.as_array(bytePointer, shape=(surface.contents.h, surface.contents.w, surface.contents.format.contents.BytesPerPixel))
        for y in range(0, surface.contents.h):
            for x in range(0, surface.contents.w):
                renderer.render(self, ctypes.addressof(surface.contents), x, y)
        SDL_UnlockSurface(surface)
        SDL_UpdateWindowSurface(self.__window)
      
    def renderPixel(self, data, x, y, width, height):
        self._ray_texture[0][y][x] = [*self._camera_position, 1.0]
        half_screen = numpy.array([width * 0.5, height * 0.5], dtype=numpy.float32)
        rel_coords = (numpy.array([x, height - y], dtype=numpy.float32) - half_screen) / half_screen
        rect_coords = rel_coords * self._view_size
        rect_point = self._screen_center + rect_coords[0] * self._camera_right + rect_coords[1] * self._camera_up
        ray_direction = rect_point - self._camera_position
        ray_direction /= numpy.linalg.norm(ray_direction)
        self._ray_texture[1][y][x] = [*ray_direction, 1.0]
        self._raytrace_texture[0][y][x] = numpy.array([0, 0, 0, 0], dtype=numpy.float32)
        self._raytrace_texture[1][y][x] = numpy.array([0, 0, 0, 0], dtype=numpy.float32)
        self._raytrace_texture[2][y][x] = numpy.array([0, 0, 0, math.inf], dtype=numpy.float32)
        self._raytrace_texture[3][y][x] = numpy.array([0, 0, 0, 0], dtype=numpy.float32)
        
        cube_indices = self._cube_indices
        cube_vertices = self._cube_vertices
        for index in range(0, len(cube_indices), 3):
            triangle = [[cube_vertices[k*8:k*8+3], cube_vertices[k*8+3:k*8+6], cube_vertices[k*8+6:k*8+8]] for k in cube_indices[index:index+3]]
            self.renderTriangle(triangle, x, y)
        
        data[y][x] = numpy.multiply([*self._raytrace_texture[0][y][x][0:3], 1.0], 255)
        
            
    def renderTriangle(self, triangle, x, y):
        ray_origin = self._ray_texture[0][y][x][0:3]
        ray_direction = self._ray_texture[1][y][x][0:3]
        A = triangle[0][0]
        B = triangle[1][0]
        C = triangle[2][0]
        AC = C - A
        BC = C - B
        AB = B - A
        N = numpy.cross(AC, BC)
        N /= numpy.linalg.norm(N)
        ND = numpy.dot(N, ray_direction[0:3])
        if (ND > 0):
            ND -= ND
            N = -N
        plane_coeff = numpy.dot(N, C)
        distance = (plane_coeff - numpy.dot(N, ray_origin)) / ND
        if not math.isfinite(distance) or distance < 0.0:
            return
        
        p = ray_origin + distance * ray_direction
        barycentric = numpy.array([
            numpy.dot(numpy.cross(AB, p - A), N) / numpy.dot(numpy.cross(AB, AC), N),
            numpy.dot(numpy.cross(BC, p - B), N) / numpy.dot(numpy.cross(BC, AB), N),
            1.0
        ], dtype=numpy.float32)
        barycentric[2] = 1.0 - barycentric[0] - barycentric[1]
        if barycentric[0] < 0.0 or barycentric[1] < 0.0 or barycentric[2] < 0.0:
            return
        
        current_distance = self._raytrace_texture[2][y][x][3]
        
        if current_distance < distance:
            return
        
        self._raytrace_texture[0][y][x] = [1.0, 1.0, 1.0, 1.0]
        self._raytrace_texture[1][y][x] = [*(N * 0.5 + 0.5), 1.0]
        self._raytrace_texture[2][y][x] = [*p, distance]
        self._raytrace_texture[3][y][x] = [*(-ray_direction), 1.0]
    
    def release(self):
        pass

if __name__ == '__main__':
    import sys

    def main():
        state = dragiyski.ui.getGlobalMouseState()

        display = dragiyski.ui.Display.getDisplayAt(state.x, state.y)

        window = dragiyski.ui.Window.create(
            title="CPU Raytracing",
            resizable=False,
            position=dragiyski.ui.WindowPosition(display=display, width=400, height=400)
        )
        
        RenderWorker(window)

    sys.exit(main())


