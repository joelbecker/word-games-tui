from utils import vertical_buffer, horizontal_buffer, display_cols, display_rows

NO_PUZZLE_MESSAGE = "No puzzle available today."


def placeholder_scene(stdscr, content="Coming soon!"):
    stdscr.timeout(-1)
    stdscr.clear()
    while True:
        vbuffer = vertical_buffer(1, display_rows(stdscr))
        hbuffer = horizontal_buffer(len(content) + 1, display_cols(stdscr))
        stdscr.addstr(vbuffer, hbuffer, content)
        stdscr.refresh()
        key = stdscr.getch()
        if key == ord('q'):
            stdscr.clear()
            break
