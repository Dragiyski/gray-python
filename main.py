import sys
import dragiyski.ui
from OpenGL.GL import *


def print_screen_info():
    print('monitor.length = %s' % len(dragiyski.ui.Display))
    for display in dragiyski.ui.Display:
        print('moditor[%d] = %s' % (display.index(), display.name()))
        print(f'  .current-mode = {display.current_mode()}')
        print(f'  .native-mode = {display.native_mode()}')
        print(f'  .bounds = {display.bounds()}')
        print(f'  .usable_bounds = {display.usable_bounds()}')
        print(f'  .dpi = {display.dpi()}')
        modes = display.modes()
        for mode_index in range(len(modes)):
            print(f'  .mode[{mode_index}]: {modes[mode_index]}')


def main():
    window = dragiyski.ui.OpenGLWindow.create(
        title='Test Window',
        context_version_major=4,
        context_version_minor=6,
        profile_mask=dragiyski.ui.OpenGLWindow.ProfileMask.CORE
    )
    window.add_event_listener('exposed', on_window_exposed)

def on_window_exposed(window):
    window.makeCurrent()
    glClearColor(0.0, 0.0, 0.0, 1.0)
    paint_window(window)
    window.releaseCurrent()

def paint_window(window):
    window.makeCurrent()
    glClear(GL_COLOR_BUFFER_BIT)

    window.swap()
    window.releaseCurrent()

if __name__ == '__main__':
    sys.exit(main())
