import curses
from palette import Palette

def main(stdscr):

    curses.use_default_colors()
    for i in range(0, curses.COLORS-1):
            curses.init_pair(i + 1, i, -1)

    curses.curs_set(0)
    stdscr.nodelay(1)
    
    options = {
        "WORDLE": Palette.green(),
        "CONNECTIONS": Palette.purple(),
        "MINI": Palette.blue(),
        "STRANDS": Palette.red(),
        "SPELLINGBEE": Palette.yellow()
    }
    current_option = 0

    while True:
        stdscr.clear()
        for idx, option in enumerate(options.keys()):
            if idx == current_option:
                stdscr.addstr(f"> {option}\n", options[option] | curses.A_BOLD)
            else:
                stdscr.addstr(f"  {option}\n", Palette.white())
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP or key == ord('k'):
            current_option = (current_option - 1) % len(options)
        elif key == curses.KEY_DOWN or key == ord('j'):
            current_option = (current_option + 1) % len(options)
        elif key == ord('q'):
            break

curses.wrapper(main)