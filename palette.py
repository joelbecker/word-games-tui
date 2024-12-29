import curses

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
