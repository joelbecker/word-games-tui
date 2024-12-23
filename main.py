import curses

WORDLE = """
                 _ _
 _ _ _ ___ ___ _| | |___ 
| | | | . |  _| . | | -_|
|_____|___|_| |___|_|___|
"""
CONNECTIONS = """
                         _   _
 ___ ___ ___ ___ ___ ___| |_|_|___ ___ ___ 
|  _| . |   |   | -_|  _|  _| | . |   |_ -|
|___|___|_|_|_|_|___|___|_| |_|___|_|_|___|
"""
MINI = """
       _     
 _____|_|___|_|
|     | |   | |
|_|_|_|_|_|_|_|
"""
STRANDS = """
     _                 _     
 ___| |_ ___ ___ ___ _| |___ 
|_ -|  _|  _| .'|   | . |_ -|
|___|_| |_| |__,|_|_|___|___|
"""
SPELLINGBEE = """
             _ _ _            _           
 ___ ___ ___| | |_|___ ___   | |_ ___ ___ 
|_ -| . | -_| | | |   | . |  | . | -_| -_|
|___|  _|___|_|_|_|_|_|_  |  |___|___|___|
    |_|               |___|               
"""

SELECTED = "\n".join(["  ", "  ", r"\\", r"//", "  "])
NOT_SELECTED = "\n".join(["  ", "  ", "  ", "  ", "  "])

def text_zip(s1, s2):
    return "\n".join([" ".join(t) for t in zip(s1.split("\n"), s2.split("\n"))])

print(text_zip(SELECTED, WORDLE.strip("\n")))
print(text_zip(NOT_SELECTED, CONNECTIONS.strip("\n")))
print(text_zip(NOT_SELECTED, MINI.strip("\n")))
print(text_zip(NOT_SELECTED, STRANDS.strip("\n")))
print(text_zip(NOT_SELECTED, SPELLINGBEE.strip("\n")))

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    
    options = [WORDLE, CONNECTIONS, MINI, STRANDS, SPELLINGBEE]
    current_option = 0

    while True:
        stdscr.clear()
        for idx, option in enumerate(options):
            if idx == current_option:
                stdscr.addstr(text_zip(SELECTED, option.strip("\n")) + "\n")
            else:
                stdscr.addstr(text_zip(NOT_SELECTED, option.strip("\n")) + "\n")
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            current_option = (current_option - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % len(options)
        elif key == ord('q'):
            break

curses.wrapper(main)