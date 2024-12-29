import curses
from connections.scene import connections_main

if __name__ == "__main__":
    curses.wrapper(connections_main)
