import sys
import dragiyski.ui


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
    mainWindow = dragiyski.ui.OpenGLWindow.create(title='test')
    mainWindowRef = dragiyski.ui.Window(mainWindow.id())
    print(mainWindowRef is mainWindow)


if __name__ == '__main__':
    sys.exit(main())
