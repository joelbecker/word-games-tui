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
