"""Full-screen info panel shared by every game (word lists, controls).

The panel replaces the game screen until a key closes it. The caller
redraws its own screen afterwards.
"""
import curses
import textwrap

import utils

CTRL_K = 11
CONTROLS_KEY = ord("0")


def show(stdscr, title: str, pages: list, color: int, page_key: int = None):
    """Show pages of body lines, each line a list of (text, attr) parts.

    page_key (if given) moves to the next page, wrapping round; any other
    key closes the panel. The closing key is consumed, not passed on.
    """
    pages = pages or [[]]
    page = 0
    stdscr.timeout(-1)
    while True:
        _draw(stdscr, title, pages, page, color, page_key)
        key = stdscr.getch()
        if page_key is not None and key == page_key and len(pages) > 1:
            page = (page + 1) % len(pages)
        elif page_key is not None and key == page_key:
            continue
        else:
            stdscr.clear()
            return


def _draw(stdscr, title, pages, page, color, page_key):
    stdscr.clear()
    lines = pages[page]
    body_width = max((sum(len(text) for text, _ in line) for line in lines), default=0)
    footer_rows = 2 if len(pages) > 1 else 1
    height = 2 + len(lines) + 1 + footer_rows
    top = max(0, utils.vertical_buffer(height, utils.display_rows(stdscr)))
    left = max(0, utils.horizontal_buffer(body_width, utils.display_cols(stdscr)))

    stdscr.addstr(top, 0, utils.center_text(stdscr, title), color | curses.A_BOLD)
    for i, line in enumerate(lines):
        x = left
        for text, attr in line:
            stdscr.addstr(top + 2 + i, x, text, attr)
            x += len(text)

    footer = top + 2 + len(lines) + 1
    if len(pages) > 1:
        stdscr.addstr(footer, 0, utils.center_text(stdscr, f"page {page + 1} of {len(pages)}"), utils.Palette.gray())
        hint = f"[{chr(page_key)}] next page · any key closes"
        stdscr.addstr(footer + 1, 0, utils.center_text(stdscr, hint), utils.Palette.gray())
    else:
        stdscr.addstr(footer, 0, utils.center_text(stdscr, "any key closes"), utils.Palette.gray())
    stdscr.refresh()


def show_controls(stdscr, game_name: str, controls: list, color: int):
    """Controls panel: controls is a list of (keys, description) pairs."""
    key_width = max(len(keys) for keys, _ in controls) + 4
    # Wrap descriptions that do not fit, indenting the rest under the first line
    desc_width = max(10, utils.display_cols(stdscr) - key_width - 2)
    lines = []
    for keys, description in controls:
        for i, text in enumerate(textwrap.wrap(description, desc_width) or [""]):
            lines.append([((keys if i == 0 else "").ljust(key_width), color), (text, utils.Palette.white())])
    show(stdscr, f"{game_name} controls", [lines], color)
