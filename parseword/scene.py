"""Parseword (layout: parseword/mockup.txt)."""
import curses

import info_panel
import store
import utils
from placeholder_scene import placeholder_scene, NO_PUZZLE_MESSAGE
from parseword.game import ParsewordGame
from parseword.scrape import load_parseword_data

CONTROLS = [
    ("h/l k/j", "previous / next word"),
    ("s", "select / deselect a word"),
    ("c", "clear the selection"),
    ("enter", "moves for the selection or word"),
    ("h / l", "in the moves: previous / next"),
    ("k / j", "in the moves: previous / next kind"),
    ("enter", "in the moves: make the move"),
    ("backspace", "back, deselect, or undo"),
    ("0", "controls"),
    ("ctrl+c", "back to menu"),
]
BACKSPACE_KEYS = (curses.KEY_BACKSPACE, curses.KEY_DC, 127, 8)
ENTER_KEYS = (curses.KEY_ENTER, 10, 13)


def wrap(parts, width):
    """Wrap [(text, attr), ...] at part boundaries into lines of at most width
    columns (a part longer than width gets a line of its own and is clipped)."""
    lines, line, used = [], [], 0
    for text, attr in parts:
        needed = len(text) + (1 if line else 0)
        if line and used + needed > width:
            lines.append(line)
            line, used = [], 0
            needed = len(text)
        if line:
            line.append((" ", utils.Palette.white()))
        line.append((text, attr))
        used += needed
    if line:
        lines.append(line)
    return lines


class ParsewordScene:
    def __init__(self, record):
        self.record = record
        progress = record["progress"]
        self.game = ParsewordGame(record["puzzle"], progress.get("steps", []))
        self.cursor = self._first_selectable()
        self.selection = []       # Selected token indices, always adjacent
        self.groups = None        # Moves on offer while choosing one
        self.option_cursor = 0
        self.auto_selected = False  # The selection was made by Enter on a word

    # Words

    def _first_selectable(self, start=0, step=1):
        i = start
        while 0 <= i < len(self.game.tokens):
            if self.game.selectable(i):
                return i
            i += step
        return None

    def move(self, step):
        if self.cursor is None:
            return
        i = self._first_selectable(self.cursor + step, step)
        if i is not None:
            self.cursor = i

    def toggle_select(self):
        self.auto_selected = False
        i = self.cursor
        if i is None:
            return
        if i in self.selection:
            # Deselecting splits the selection; keep the part before it
            self.selection = [j for j in self.selection if j < i]
        elif self.selection and (i == self.selection[0] - 1 or i == self.selection[-1] + 1):
            self.selection = sorted(self.selection + [i])
        else:
            self.selection = [i]

    def selection_options(self):
        if not self.selection:
            return []
        return self.game.options(self.selection[0], self.selection[-1] + 1)

    def choose_move(self):
        if not self.selection and self.cursor is not None:
            # Enter on an unselected word selects it, if it has moves
            if not self.game.options(self.cursor, self.cursor + 1):
                return
            self.selection = [self.cursor]
            self.auto_selected = True
        groups = self.selection_options()
        if groups:
            self.groups, self.option_cursor = groups, 0

    def clear_selection(self):
        self.groups, self.selection = None, []

    # Moves

    @property
    def flat_options(self):
        return [(g, o) for g, (_, _, opts) in enumerate(self.groups) for o in opts]

    def move_option(self, step):
        self.option_cursor = (self.option_cursor + step) % len(self.flat_options)

    def move_group(self, step):
        flat = self.flat_options
        group = (flat[self.option_cursor][0] + step) % len(self.groups)
        self.option_cursor = next(k for k, (g, _) in enumerate(flat) if g == group)

    def make_move(self):
        _, option = self.flat_options[self.option_cursor]
        start = self.selection[0]
        self.game.apply({"start": start, "end": self.selection[-1] + 1, "result": option.result,
                         "type": option.kind, "indicator": option.indicator})
        self.groups, self.selection, self.cursor = None, [], start
        self.save()

    def back(self):
        if self.groups is not None:
            self.groups = None
            if self.auto_selected:  # Enter made the selection, so undo that too
                self.selection, self.auto_selected = [], False
        elif self.selection:
            self.selection = []
        else:
            step = self.game.undo()
            if step:
                self.cursor = step["start"]
                self.save()

    def save(self):
        steps = [{k: s[k] for k in ("start", "end", "result", "type", "indicator")} for s in self.game.steps]
        store.save_progress(self.record, {"steps": steps, "solved": self.game.is_solved})

    # Display

    def _token_attr(self, i, token, show_cursor=True):
        attr = utils.Palette.teal() if token.transformed else utils.Palette.white()
        if token.definition:
            attr |= curses.A_UNDERLINE
        if i in self.selection:
            attr = utils.Palette.teal() | curses.A_REVERSE
            if self.groups is not None and self._is_indicator(i):
                attr |= curses.A_UNDERLINE
        if show_cursor and i == self.cursor and self.groups is None:
            attr |= curses.A_REVERSE | curses.A_BOLD
        return attr

    def _is_indicator(self, i):
        group = self.flat_options[self.option_cursor][0]
        return i - self.selection[0] in self.groups[group][1]

    def _phrase_parts(self, show_cursor=True):
        return [(t.text.upper() if t.transformed else t.text, self._token_attr(i, t, show_cursor))
                for i, t in enumerate(self.game.tokens)]

    def _option_lines(self, groups, width, choosing, empty="No moves for this selection"):
        """The moves for the selection; the cursor is shown while choosing."""
        if not groups:
            return [[], [(empty, utils.Palette.gray())]]
        lines = []
        index = 0 if choosing else -1
        for heading, _, opts in groups:
            lines.append([])
            lines.append([(heading, utils.Palette.gray())])
            parts = []
            for k, option in enumerate(opts):
                attr = utils.Palette.white()
                if choosing and index == self.option_cursor:
                    attr |= curses.A_REVERSE | curses.A_BOLD
                text = option.result.upper()
                parts.append((text + (" /" if k < len(opts) - 1 else ""), attr))
                if choosing:
                    index += 1
            lines += self._split_slashes(wrap(parts, width))
        return lines

    @staticmethod
    def _split_slashes(lines):
        """Draw the " /" separators unhighlighted."""
        out = []
        for line in lines:
            parts = []
            for text, attr in line:
                if text.endswith(" /"):
                    parts += [(text[:-2], attr), (" /", utils.Palette.gray())]
                else:
                    parts.append((text, attr))
            out.append(parts)
        return out

    def _step_lines(self, width):
        lines = [[]]
        for step in self.game.steps:
            words = step["before"].split()
            indicator = set(step["indicator"].split()) if step.get("indicator") else set()
            parts = [(w, utils.Palette.white() | (curses.A_UNDERLINE if w in indicator else 0)) for w in words]
            parts += [("->", utils.Palette.gray()), (step["result"].lower(), utils.Palette.teal())]
            lines += wrap(parts, width)
        return lines

    def draw(self, stdscr):
        stdscr.clear()
        width = utils.display_cols(stdscr)
        solved = self.game.is_solved
        lines = wrap(self._phrase_parts(show_cursor=not solved), width)
        if solved:
            lines += self._step_lines(width)
        elif self.groups is not None:
            lines += self._option_lines(self.groups, width, choosing=True)
        elif self.selection:
            lines += self._option_lines(self.selection_options(), width, choosing=False)
        elif self.cursor is not None:
            # Nothing selected: preview the moves for the word under the cursor
            lines += self._option_lines(self.game.options(self.cursor, self.cursor + 1), width,
                                        choosing=False, empty="No moves for this word")

        top = max(0, utils.vertical_buffer(len(lines), utils.display_rows(stdscr)))
        cols = stdscr.getmaxyx()[1]
        for row, line in enumerate(lines):
            x = max(0, (min(cols, width) - sum(len(t) for t, _ in line)) // 2)
            for text, attr in line:
                stdscr.addstr(top + row, x, text, attr)
                x += len(text)
        stdscr.refresh()

    # Input

    def handle(self, key):
        if self.game.is_solved:
            return  # Solved puzzles are locked
        if self.groups is not None:
            if key in (ord("h"), curses.KEY_LEFT):
                self.move_option(-1)
            elif key in (ord("l"), curses.KEY_RIGHT):
                self.move_option(1)
            elif key in (ord("j"), curses.KEY_DOWN):
                self.move_group(1)
            elif key in (ord("k"), curses.KEY_UP):
                self.move_group(-1)
            elif key in ENTER_KEYS:
                self.make_move()
            elif key in BACKSPACE_KEYS:
                self.back()
            elif key == ord("c"):
                self.clear_selection()
            return
        if key in (ord("h"), ord("k"), curses.KEY_LEFT):
            self.move(-1)
        elif key in (ord("l"), ord("j"), curses.KEY_RIGHT):
            self.move(1)
        elif key == ord("s"):
            self.toggle_select()
        elif key == ord("c"):
            self.clear_selection()
        elif key in ENTER_KEYS:
            self.choose_move()
        elif key in BACKSPACE_KEYS:
            self.back()


def parseword_scene(stdscr):
    curses.curs_set(0)
    stdscr.clear()

    record = load_parseword_data(stdscr)
    if record is None:
        return placeholder_scene(stdscr, NO_PUZZLE_MESSAGE)

    scene = ParsewordScene(record)
    scene.draw(stdscr)
    stdscr.timeout(-1)  # The loading screen leaves input non-blocking
    try:
        while True:
            key = stdscr.getch()
            if key == info_panel.CONTROLS_KEY:
                info_panel.show_controls(stdscr, "Parseword", CONTROLS, utils.Palette.teal())
            elif key == curses.KEY_RESIZE:
                pass
            else:
                scene.handle(key)
            scene.draw(stdscr)
    except KeyboardInterrupt:
        stdscr.clear()
        stdscr.refresh()
        return
