import curses
from connections.scene import connections_scene

if __name__ == "__main__":
    curses.wrapper(connections_scene)
