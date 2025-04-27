import utils
import curses
from utils import Palette
from typing import Callable
from dataclasses import dataclass

from wordle.scene import wordle_scene
from mini.scene import mini_scene
from connections.scene import connections_scene
from spellingbee.scene import spellingbee_scene
from placeholder_scene import placeholder_scene

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
        WordGame("mini", mini_scene, Palette.blue()),
        WordGame("strands", placeholder_scene, Palette.red()),
        WordGame("spellingbee", spellingbee_scene, Palette.yellow())
    ]
    
    current_option = 0
    vbuffer = utils.vertical_buffer(len(games), utils.display_rows(stdscr))
    hbuffer = utils.horizontal_buffer(max(len(game.name) for game in games), utils.display_cols(stdscr))
    stdscr.clear()
    try:
        while True:
            for idx, option in enumerate(games):
                if idx == current_option:
                    stdscr.addstr(vbuffer+idx, hbuffer, f"> {option.name.upper()}\n", option.color | curses.A_BOLD)
                else:
                    stdscr.addstr(vbuffer+idx, hbuffer, f"  {option.name.upper()}\n", Palette.white())
            
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
    except KeyboardInterrupt:
        exit

curses.wrapper(main)
