import providers
from loading_scene import run_loading_animation


def load_mini_data(stdscr):
    stdscr.clear()
    return run_loading_animation(stdscr, lambda: providers.get_puzzle("mini"), "Fetching Mini crossword...")
