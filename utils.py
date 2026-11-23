import re
import curses

WIDTH = 50


MAX_ROWS = 24  # Screens are laid out in a box of at most this size,
MAX_COLS = 60  # centred on the terminal


class SafeWindow:
    """Wraps the curses screen so that every scene draws in a box of at most
    MAX_ROWS x MAX_COLS centred on the terminal, and drawing outside that box
    never crashes.

    Coordinates passed to addstr are relative to the box, and getmaxyx returns
    the box's size, so scenes centre their content within it. Text above, below
    or left of the box is dropped, and text running past its right edge is cut
    off. Everything else is passed through.
    """

    def __init__(self, window):
        self._window = window

    def __getattr__(self, name):
        return getattr(self._window, name)

    def _box(self):
        """(top, left, rows, cols) of the content box on the terminal."""
        rows, cols = self._window.getmaxyx()
        box_rows, box_cols = min(rows, MAX_ROWS), min(cols, MAX_COLS)
        return (rows - box_rows) // 2, (cols - box_cols) // 2, box_rows, box_cols

    def getmaxyx(self):
        return self._box()[2:]

    def addstr(self, *args):
        if len(args) >= 3 and isinstance(args[0], int) and isinstance(args[1], int):
            y, x, text, *attr = args
            top, left, rows, cols = self._box()
            text = str(text)
            if x < 0:
                text, x = text[-x:], 0
            text = text[:max(0, cols - x)]
            if not text or not 0 <= y < rows:
                return
            args = (top + y, left + x, text, *attr)
        try:
            self._window.addstr(*args)
        except curses.error:
            pass  # e.g. writing the bottom-right cell, which curses reports as an error after drawing it


def strip_ansi(s):
    return re.sub(r'\x1b[^m]*m', '', s)
     

def justify(s, block=15, width=WIDTH, justify='left'):
    _justify = {
        'left': str.ljust,
        'right': str.rjust,
        'center': str.center
    }[justify]
    reference = strip_ansi(s)
    justified = _justify(reference, block or 0, ' ')
    centered = justified.center(width, ' ')
    result = centered.replace(reference, s)
    return result

def center_text(stdscr, text):
    return justify(text, justify='center', width=display_cols(stdscr))

def display_rows(stdscr):
    return min(stdscr.getmaxyx()[0], MAX_ROWS)
    

def display_cols(stdscr):
    return min(stdscr.getmaxyx()[1], MAX_COLS)


def vertical_buffer(content_rows, display_rows):
    return (display_rows - content_rows) // 2


def horizontal_buffer(content_cols, display_cols):
    return (display_cols - content_cols) // 2


def fit_rows(stdscr, content_rows, gaps):
    """Centre a screen of content_rows rows plus `gaps` blank spacer rows.

    Returns (top, gap): gap is 1 when everything fits and 0 on screens too
    short for the spacers, so content is never pushed off the screen by them.
    """
    rows = display_rows(stdscr)
    gap = 1 if content_rows + gaps <= rows else 0
    return max(0, vertical_buffer(content_rows + gaps * gap, rows)), gap


class Palette:

    @staticmethod
    def from_name(name):
        return getattr(Palette, name)()

    @staticmethod
    def purple():
        return curses.color_pair(170)

    @staticmethod
    def yellow():
        return curses.color_pair(227)

    @staticmethod
    def green():
        return curses.color_pair(43)

    @staticmethod
    def blue():
        return curses.color_pair(26)

    @staticmethod
    def red():
        return curses.color_pair(203)

    @staticmethod
    def teal():
        return curses.color_pair(38)

    @staticmethod
    def white():
        return curses.color_pair(253)

    @staticmethod
    def gray():
        return curses.color_pair(240)
