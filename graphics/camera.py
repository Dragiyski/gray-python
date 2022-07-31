import math
import numpy
import threading


class MouseCamera:
    def __init__(self, *, x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0, roll=0.0, world_front=[0.0, 1.0, 0.0], world_up=[0.0, 0.0, 1.0], width=800, height=600, field_of_view=numpy.deg2rad(60.0), screen_distance=1.0):
        self.position = numpy.array([x, y, z], dtype=numpy.float32)
        self.world_front = numpy.array(list(world_front), dtype=numpy.float32)
        self.world_up = numpy.array(list(world_up), dtype=numpy.float32)

        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

        self.view_front = world_front.copy()
        self.view_up = world_up.copy()
        self.view_right = numpy.cross(self.view_front, self.view_up)

        self.screen_width = width
        self.screen_height = height
        self.lock = threading.RLock()

        self.screen_distance = screen_distance
        self.field_of_view = field_of_view

        self.update()

    def update(self):
        with self.lock:
            cos_yaw = math.cos(self.yaw)
            sin_yaw = math.sin(self.yaw)
            cos_pitch = math.cos(self.pitch)
            sin_pitch = math.sin(self.pitch)
            cos_roll = math.cos(self.roll)
            sin_roll = math.sin(self.roll)

            mat_yaw = numpy.array([
                [cos_yaw, sin_yaw, 0.0],
                [-sin_yaw, cos_yaw, 0.0],
                [0.0, 0.0, 1.0]
            ], dtype=numpy.float32)

            mat_pitch = numpy.array([
                [1.0, 0.0, 0.0],
                [0.0, cos_pitch, sin_pitch],
                [0.0, -sin_pitch, cos_pitch]
            ], dtype=numpy.float32)

            mat_roll = numpy.array([
                [cos_roll, 0.0, -sin_roll],
                [0.0, 1.0, 0.0],
                [sin_roll, 0.0, cos_roll]
            ], dtype=numpy.float32)

            mat = numpy.matmul(numpy.matmul(mat_yaw, mat_pitch), mat_roll)
            self.view_front = numpy.matmul(mat, self.world_front)
            self.view_up = numpy.matmul(mat, self.world_up)
            self.view_right = numpy.cross(self.view_front, self.view_up)

            half_diagonal = math.atan(self.field_of_view / 2.0) * self.screen_distance
            aspect_ratio = self.screen_width / self.screen_height
            self.view_height = half_diagonal / math.sqrt(1 + aspect_ratio ** 2)
            self.view_width = aspect_ratio * self.view_height

    def set_screen_size(self, width: int, height: int):
        with self.lock:
            self.screen_width = width
            self.screen_height = height
            self.update()

    def rotate(self, delta_yaw: float, delta_pitch: float):
        self.yaw = (self.yaw + delta_yaw) % (math.pi * 2)
        self.pitch = max(min(self.pitch + delta_pitch, math.pi / 2), -math.pi / 2)
        self.update()