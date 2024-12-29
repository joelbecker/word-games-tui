from datetime import datetime
from utils import vertical_buffer, horizontal_buffer, display_cols, display_rows

def placeholder_scene(stdscr):
    stdscr.nodelay(True)
    stdscr.clear()
    content = "Coming soon!"
    while True:
        vbuffer = vertical_buffer(1, display_rows(stdscr))
        hbuffer = horizontal_buffer(len(content) + 1, display_cols(stdscr))
        stdscr.addstr(vbuffer, hbuffer, content)
        stdscr.refresh()
        key = stdscr.getch()
        if key == ord('q'):
            break