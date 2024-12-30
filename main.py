import curses
from dataclasses import dataclass

from utils import Palette
from typing import Callable
from placeholder_scene import placeholder_scene
from connections.scene import connections_scene
from wordle.scene import wordle_scene


@dataclass
class WordGame:
    name: str
    func: Callable
    color: int


def main(stdscr):

    curses.use_default_colors()
    for i in range(0, curses.COLORS-1):
            curses.init_pair(i + 1, i, -1)

    curses.curs_set(0)
    stdscr.nodelay(1)
    
    games = [
        WordGame("wordle", wordle_scene, Palette.green()),
        WordGame("connections", connections_scene, Palette.purple()),
        WordGame("mini", placeholder_scene, Palette.blue()),
        WordGame("strands", placeholder_scene, Palette.red()),
        WordGame("spellingbee", placeholder_scene, Palette.yellow())
    ]
    
    current_option = 0
    
    stdscr.clear()

    while True:
        for idx, option in enumerate(games):
            if idx == current_option:
                stdscr.addstr(idx, 0, f"> {option.name.upper()}\n", option.color | curses.A_BOLD)
            else:
                stdscr.addstr(idx, 0, f"  {option.name.upper()}\n", Palette.white())
        
        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP or key == ord('k'):
            current_option = (current_option - 1) % len(games)
        elif key == curses.KEY_DOWN or key == ord('j'):
            current_option = (current_option + 1) % len(games)
        elif key == ord('q'):
            break
        elif key == ord('\n'):
            stdscr.clear()
            stdscr.refresh()
            games[current_option].func(stdscr)

curses.wrapper(main)
