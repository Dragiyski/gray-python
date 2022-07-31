import math
import numpy

position = numpy.array([0.0, 0.0, 0.0], dtype=numpy.float32)
# Default front vector is to the North at the horizon.
world_front = numpy.array([0.0, 1.0, 0.0], dtype=numpy.float32)
world_up = numpy.array([0.0, 0.0, 1.0], dtype=numpy.float32)
yaw = 0.0
pitch = 0.0
roll = 0.0
view_front = world_front.copy()
view_up = world_up.copy()
view_right = numpy.cross(view_front, view_up)
pixel_width = 800
pixel_height = 600
field_of_view = numpy.deg2rad(60.0)
view_width = 1.0
view_height = 1.0

def update_camera():
    global view_front, view_up, view_right, view_width, view_height
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    cos_roll = math.cos(roll)
    sin_roll = math.sin(roll)
    
    # Yaw rotation is inversed: mathematical rotation is counter-clockwise, which means:
    # rotation(parameter) with increase of parameter, rotation will turn left (not right)
    # As mouse X component increase moving the mouse to the right, this means, moving the mouse to the right
    # will rotate to the left... Thus we invert X rotation.
    mat_yaw = numpy.array([
        [cos_yaw, sin_yaw, 0.0],
        [-sin_yaw, cos_yaw, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=numpy.float32)
    
    # Mouse Y parameter matches counter-clockwise rotation, so no inversion needed.
    mat_pitch = numpy.array([
        [1.0, 0.0, 0.0],
        [0.0, cos_pitch, -sin_pitch],
        [0.0, sin_pitch, cos_pitch]
    ], dtype=numpy.float32)
    
    # If roll is initiated by mouse X parameter, increasing X must do clockwise rotation,
    # so roll is inverted.
    mat_roll = numpy.array([
        [cos_roll, 0.0, -sin_roll],
        [0.0, 1.0, 0.0],
        [sin_roll, 0.0, cos_roll]
    ], dtype=numpy.float32)
    
    mat = numpy.matmul(numpy.matmul(mat_yaw, mat_pitch), mat_roll)
    view_front = numpy.matmul(mat, world_front)
    view_up = numpy.matmul(mat, world_up)
    view_right = numpy.cross(view_front, view_up)
    
    half_diagonal = math.atan(field_of_view / 2.0)
    aspect_ratio = pixel_width / pixel_height
    view_height = half_diagonal / math.sqrt(1 + aspect_ratio ** 2)
    view_width = aspect_ratio * view_height

if __name__ == '__main__':
    import sys
    assert len(sys.argv) >= 3
    yaw = numpy.deg2rad(float(sys.argv[1]))
    pitch = numpy.deg2rad(float(sys.argv[2]))
    roll = 0.0
    if len(sys.argv) >= 4:
        rot_roll = numpy.deg2rad(float(sys.argv[3]))
    update_camera()
    numpy.set_printoptions(floatmode='fixed', precision=3, sign=' ')
    print(f'front = {view_front}')
    print(f'   up = {view_up}')
    print(f'right = {view_right}')
    