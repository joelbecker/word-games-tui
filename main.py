import curses


def main(stdscr):

    curses.use_default_colors()
    for i in range(0, curses.COLORS-1):
            curses.init_pair(i + 1, i, -1)

    # Define color pairs
    PURPLE = curses.color_pair(170)
    YELLOW = curses.color_pair(227)
    GREEN = curses.color_pair(43)
    BLUE = curses.color_pair(26)
    RED = curses.color_pair(203)
    WHITE = curses.color_pair(253)
    GRAY = curses.color_pair(240)
    
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    
    options = {
        "WORDLE": GREEN,
        "CONNECTIONS": PURPLE,
        "MINI": BLUE,
        "STRANDS": RED,
        "SPELLINGBEE": YELLOW
    }
    current_option = 0

    while True:
        stdscr.clear()
        for idx, option in enumerate(options.keys()):
            if idx == current_option:
                stdscr.addstr(f"> {option}\n", options[option] | curses.A_BOLD)
            else:
                stdscr.addstr(f"  {option}\n", WHITE)
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP or key == ord('k'):
            current_option = (current_option - 1) % len(options)
        elif key == curses.KEY_DOWN or key == ord('j'):
            current_option = (current_option + 1) % len(options)
        elif key == ord('q'):
            break

curses.wrapper(main)