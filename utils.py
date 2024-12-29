import curses
import re


WIDTH = 50


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


def display_rows(stdscr):
    return min(stdscr.getmaxyx()[0], 24)
    

def display_cols(stdscr):
    return min(stdscr.getmaxyx()[1], 60)


def vertical_buffer(content_rows, display_rows):
    return (display_rows - content_rows) // 2


def horizontal_buffer(content_cols, display_cols):
    return (display_cols - content_cols) // 2


class Palette:

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
    def white():
        return curses.color_pair(253)

    @staticmethod
    def gray():
        return curses.color_pair(240)
