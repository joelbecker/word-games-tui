import re
import sys
import tty
import termios


WIDTH = 50

def print_banner(s):
    r = WIDTH - len(s) - 2
    leftr = r//2
    rightr = r - leftr
    print("-"*leftr + " " + s + " " + "-"*rightr)
    print()


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


def print_center(s, block=15, width=WIDTH):
    print(justify(s, block, width))


def clear_display():
    print("\033c")


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch