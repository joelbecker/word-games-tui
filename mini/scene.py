from dataclasses import dataclass
import time
import curses
import curses.ascii
import textwrap
from typing import Iterable, Callable

import info_panel
import store
import utils
from mini.scrape import load_mini_data
from placeholder_scene import placeholder_scene, NO_PUZZLE_MESSAGE


@dataclass
class CrosswordClue:
    number: str
    clue: str
    is_across: bool

    def __str__(self):
        return f"{self.number}{'A' if self.is_across else 'D'} {self.clue}"

@dataclass
class CrosswordCell:
    i: int
    j: int
    solution: str
    number: str = " "
    is_circled: bool = False
    value: str = " "
    is_filled: bool = False
    is_out_of_bounds: bool = False
    across_clue: CrosswordClue = None
    down_clue: CrosswordClue = None

    def __post_init__(self):
        assert self.value is not None

    def set_value(self, value: str):
        assert len(value) == 1, "Value must be a single character"
        assert value.isalpha() or value == " ", "Value must be an alphabetic character or a space"
        if value == " ":
            self.is_filled = False
        else:
            self.is_filled = True
        self.value = value
    

CONTROLS = [
    ("letters", "fill the square and move on"),
    ("space", "switch across / down"),
    ("enter / tab", "next unfinished word"),
    ("shift+tab", "previous word"),
    ("backspace", "delete"),
    ("arrows", "move or switch direction"),
    ("0", "controls"),
    ("ctrl+c", "back to menu"),
]


def word_runs(cells: list[list[CrosswordCell]], across: bool) -> list[list[tuple[int, int]]]:
    """Runs of 2+ open squares in one direction, sorted by starting square
    row by row, which is clue-number order."""
    rows, cols = len(cells), len(cells[0])
    words = []
    for a in range(rows if across else cols):
        run = []
        for b in range(cols if across else rows):
            i, j = (a, b) if across else (b, a)
            if cells[i][j].is_out_of_bounds:
                if len(run) > 1:
                    words.append(run)
                run = []
            else:
                run.append((i, j))
        if len(run) > 1:
            words.append(run)
    return sorted(words)


class Crossword:
    def __init__(self, cells: list[list[CrosswordCell]]) -> None:
        # definition
        self.cells = cells
        self.rows = len(cells)
        self.cols = len(cells[0])
        
        # validation
        assert all(len(row) == self.cols for row in cells), "All rows must have the same length"
        
        # words: runs of 2+ open squares, in clue-number order
        self.across_words = word_runs(cells, across=True)
        self.down_words = word_runs(cells, across=False)

        # state: start on 1-Across
        self.cursor_h = bool(self.across_words)
        self.cursor_row, self.cursor_col = (self.across_words or self.down_words)[0][0]
        self.prev_cursor_row = self.cursor_row
        self.prev_cursor_col = self.cursor_col
        self.prev_cursor_h = self.cursor_h
        self.prev_message = ""

    @property
    def is_full(self) -> bool:
        return all(
            cell.is_filled for row in self.cells
            for cell in row if not cell.is_out_of_bounds
        )
    
    @property
    def is_solved(self) -> bool:
        return all(
            cell.is_filled and cell.value == cell.solution for row in self.cells
            for cell in row if not cell.is_out_of_bounds
        )

    def set_cell(self, i: int, j: int, c: str):
        if self.is_out_of_bounds(i, j):
            return False
        else:
            self.cells[i][j].set_value(c.upper())
            return True

    def cursor_cell(self) -> CrosswordCell:
        return self.cells[self.cursor_row][self.cursor_col]

    def is_filled(self, i: int, j: int) -> bool:
        return not self.is_out_of_bounds(i, j) and self.cells[i][j].is_filled

    def is_empty(self, i: int, j: int) -> bool:
        return not self.is_out_of_bounds(i, j) and not self.cells[i][j].is_filled

    def is_cursor_cell(self, i: int, j: int) -> bool:
        return i == self.cursor_row and j == self.cursor_col

    def word_at(self, i: int, j: int, across: bool):
        for word in (self.across_words if across else self.down_words):
            if (i, j) in word:
                return word
        return None

    def current_word(self) -> list:
        """The word under the cursor in the cursor's direction."""
        return (
            self.word_at(self.cursor_row, self.cursor_col, self.cursor_h)
            or [(self.cursor_row, self.cursor_col)]
        )

    def is_cursor_lane(self, i: int, j: int) -> bool:
        return (i, j) in self.current_word()

    def is_out_of_bounds(self, i: int, j: int) -> bool:
        return (i < 0 or j < 0 or i >= self.rows or j >= self.cols 
                or self.cells[i][j].is_out_of_bounds)

    def _check_coordinates(self, coords: list[tuple[int, int]], f: Callable[[int, int], bool], b: Callable[[Iterable[bool]], bool]):
        return b(f(i, j) for i, j in coords)
    
    def check_cursor_cells(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_cursor_cell, b)
    
    def check_cursor_lanes(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_cursor_lane, b)
    
    def check_out_of_bounds(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_out_of_bounds, b)

    def _color_character(self, i: int, j: int, c: str, rel_coords: list[tuple[int, int]]) -> tuple[chr, int]:
        _c = c
        coords = [(i + di, j + dj) for di, dj in rel_coords]
        is_white = c.isalpha() or self.check_out_of_bounds(coords)
        is_yellow = self.check_cursor_cells(coords)
        is_blue = self.check_cursor_lanes(coords)
        is_out_of_bounds = self.check_out_of_bounds(coords, all)
        
        if is_out_of_bounds:
            color = utils.Palette.gray()
        elif is_yellow:
            color = utils.Palette.yellow()
        elif is_blue:
            color = utils.Palette.blue()
        elif is_white:
            color = utils.Palette.white()
        else:
            color = utils.Palette.gray()

        return _c, color

    def _character(self, i: int, j: int, is_hline: bool, is_vline: bool, is_center: bool, is_center_left: bool, is_center_right: bool) -> tuple[chr, int]:
        if is_center:
            cell = self.cells[i][j]
            return self._color_character(i, j, cell.value if cell.is_filled else " ", [(0, 0)])
        elif is_center_left:
            cell = self.cells[i][j]
            return self._color_character(i, j, "(" if cell.is_circled else " ", [(0, 0)])
        elif is_center_right:
            cell = self.cells[i][j]
            return self._color_character(i, j, ")" if cell.is_circled else " ", [(0, 0)])
        elif is_hline and is_vline:
            rel_coords = [(0, 0), (0, -1), (-1, 0), (-1, -1)]
            return self._color_character(i, j, "+", rel_coords)
        elif is_hline:
            rel_coords = [(0, 0), (-1, 0)]
            return self._color_character(i, j, "-", rel_coords)
        elif is_vline:
            rel_coords = [(0, 0), (0, -1)]
            return self._color_character(i, j, "|", rel_coords)
        else:
            rel_coords = [(0, 0)]
            return self._color_character(i, j, " ", rel_coords)

    def update_display(self, stdscr, message: str = "", timer_seconds: int = 0, full_update: bool = False):
        def row_to_y(col: int) -> tuple[int, int]:
            return col * 2, (col + 1) * 2 + 1
        
        def col_to_x(row: int) -> tuple[int, int]:
            return row * 4, (row + 1) * 4 + 1
        
        y_start = 0
        x_start = 0
        y_end = row_to_y(self.rows - 1)[1]
        x_end = col_to_x(self.cols - 1)[1]
        hbuffer = utils.horizontal_buffer(x_end, utils.display_cols(stdscr))
        # Timer, grid, clue (up to 2 lines); the spacers go on short screens
        top, gap = utils.fit_rows(stdscr, 1 + y_end + 2, 2)
        vbuffer = top + 1 + gap

        if full_update:
            stdscr.clear()

        minutes, seconds = divmod(timer_seconds, 60)
        timer_display = f"{int(minutes):02}:{int(seconds):02}"
        stdscr.addstr(top, (utils.display_cols(stdscr) - 5)//2, timer_display)

        for y in range(y_start, y_end):
            i = y // 2
            is_hline = y % 2 == 0
            for x in range(x_start, x_end):
                if not full_update:
                    cursor_row_ys = row_to_y(self.cursor_row)
                    prev_cursor_row_ys = row_to_y(self.prev_cursor_row)
                    cursor_col_xs = col_to_x(self.cursor_col)
                    prev_cursor_col_xs = col_to_x(self.prev_cursor_col)
                    is_in_update_area = (
                        cursor_row_ys[0] <= y < cursor_row_ys[1]
                        or prev_cursor_row_ys[0] <= y < prev_cursor_row_ys[1]
                        or cursor_col_xs[0] <= x < cursor_col_xs[1]
                        or prev_cursor_col_xs[0] <= x < prev_cursor_col_xs[1]
                    )
                    if not is_in_update_area:
                        continue
                    
                j = x // 4
                is_vline = x % 4 == 0
                is_center = x % 4 == 2 and y % 2 == 1
                is_center_left = x % 4 == 1 and y % 2 == 1
                is_center_right = x % 4 == 3 and y % 2 == 1
                try:
                    c, color = self._character(i, j, is_hline, is_vline, is_center, is_center_left, is_center_right)
                    stdscr.addstr(y + vbuffer, x + hbuffer, c, color)
                except Exception as e:
                    stdscr.addstr(y + vbuffer, x + hbuffer, "#")
                    raise e

        if message != self.prev_message:
            min_lines = 3  # Blank lines clear a longer previous clue
            wrapped_lines = textwrap.wrap(message, width=utils.display_cols(stdscr) - 2)
            wrapped_lines.extend([""] * (min_lines - len(wrapped_lines)))
            for i, line in enumerate(wrapped_lines):
                stdscr.addstr(
                    y_end + vbuffer + gap + i,
                    0,
                    utils.center_text(stdscr, line),
                    utils.Palette.white()
                )

        stdscr.refresh()
    

class CrosswordController:

    def __init__(self, puzzle: Crossword, record: dict):
        self.puzzle = puzzle
        self.record = record
        # Resume the timer where the player left off
        self.start_time = time.time() - record["progress"].get("elapsed", 0)

    def save_progress(self, elapsed: float):
        store.save_progress(self.record, {
            "values": [
                "".join(cell.value if cell.is_filled else " " for cell in row)
                for row in self.puzzle.cells
            ],
            "elapsed": round(elapsed, 1),
            "solved": self.puzzle.is_solved,
        })

    # Navigation. Words are visited in clue order: across, then down.

    def go_to(self, cell, across: bool):
        """Move the cursor, switching direction if the square has no word that way."""
        i, j = cell
        if not self.puzzle.word_at(i, j, across) and self.puzzle.word_at(i, j, not across):
            across = not across
        self.puzzle.cursor_row, self.puzzle.cursor_col = cell
        self.puzzle.cursor_h = across

    def toggle_cursor_direction(self):
        i, j = self.puzzle.cursor_row, self.puzzle.cursor_col
        if self.puzzle.word_at(i, j, not self.puzzle.cursor_h):
            self.puzzle.cursor_h = not self.puzzle.cursor_h

    def first_empty(self, word):
        return next((cell for cell in word if self.puzzle.is_empty(*cell)), None)

    def next_word(self, step: int = 1):
        """Go to the next (or previous, step=-1) word with an empty square,
        or simply the next word once the grid is full."""
        order = [(w, True) for w in self.puzzle.across_words] + [(w, False) for w in self.puzzle.down_words]
        current = (self.puzzle.current_word(), self.puzzle.cursor_h)
        index = order.index(current) if current in order else -1
        candidates = [order[(index + step * k) % len(order)] for k in range(1, len(order) + 1)]
        for word, across in candidates:
            empty = self.first_empty(word)
            if empty:
                return self.go_to(empty, across)
        word, across = candidates[0]
        self.go_to(word[0], across)

    def type_letter(self, letter: str):
        word = self.puzzle.current_word()
        was_full = all(self.puzzle.is_filled(*cell) for cell in word)
        cell = (self.puzzle.cursor_row, self.puzzle.cursor_col)
        self.puzzle.set_cell(*cell, letter)
        index = word.index(cell)
        if was_full or self.puzzle.is_full:
            # Overwriting: step through the word without jumping away
            if index + 1 < len(word):
                self.go_to(word[index + 1], self.puzzle.cursor_h)
            return
        # Next empty square in this word, wrapping back to its start
        for next_cell in word[index + 1:] + word[:index]:
            if self.puzzle.is_empty(*next_cell):
                return self.go_to(next_cell, self.puzzle.cursor_h)
        self.next_word()

    def backspace(self):
        cell = (self.puzzle.cursor_row, self.puzzle.cursor_col)
        if self.puzzle.is_filled(*cell):
            self.puzzle.set_cell(*cell, " ")
            return
        word = self.puzzle.current_word()
        index = word.index(cell)
        if index > 0:
            self.go_to(word[index - 1], self.puzzle.cursor_h)
            self.puzzle.set_cell(*word[index - 1], " ")

    def arrow(self, di: int, dj: int):
        """An arrow across the current direction only switches direction (as
        in the NYT app); along it, it moves one square, skipping black squares."""
        across = di == 0
        i, j = self.puzzle.cursor_row, self.puzzle.cursor_col
        if across != self.puzzle.cursor_h and self.puzzle.word_at(i, j, across):
            self.puzzle.cursor_h = across
            return
        while True:
            i, j = i + di, j + dj
            if not (0 <= i < self.puzzle.rows and 0 <= j < self.puzzle.cols):
                return
            if not self.puzzle.is_out_of_bounds(i, j):
                return self.go_to((i, j), self.puzzle.cursor_h)

    def run(self, stdscr):
        stdscr.timeout(250)  # Wake periodically to update the timer
        nice_try_message_shown = False
        current_time = last_update_time = time.time()
        timer_seconds = current_time - self.start_time
        if self.puzzle.is_solved:
            message = "Congratulations!"
        else:
            message = str(self.puzzle.cursor_cell().across_clue)

        self.puzzle.update_display(
            stdscr,
            message=message,
            timer_seconds=timer_seconds,
            full_update=True
        )

        try:
            while True:
                if not self.puzzle.is_solved:
                    current_time = time.time()
                    timer_seconds = current_time - self.start_time

                # Check for input
                key = stdscr.getch()
                if key == info_panel.CONTROLS_KEY:
                    info_panel.show_controls(stdscr, "Mini", CONTROLS, utils.Palette.blue())
                    stdscr.timeout(250)
                    self.puzzle.prev_message = None  # Force the clue to redraw
                    self.puzzle.update_display(stdscr, message=message, timer_seconds=timer_seconds, full_update=True)
                    continue
                is_edit = key in (curses.KEY_BACKSPACE, 127, 8) or (0 <= key < 256 and curses.ascii.isalpha(key))
                if is_edit and self.puzzle.is_solved:
                    continue  # A solved puzzle is final: only moving around is allowed
                if key != -1:  # Input detected
                    self.puzzle.prev_cursor_row = self.puzzle.cursor_row
                    self.puzzle.prev_cursor_col = self.puzzle.cursor_col
                    self.puzzle.prev_cursor_h = self.puzzle.cursor_h
                    self.puzzle.prev_message = message
                    was_solved = self.puzzle.is_solved

                    if key in (curses.KEY_BACKSPACE, 127, 8):
                        self.backspace()
                    elif key in (curses.KEY_ENTER, 10, 13, 9):  # Enter or Tab
                        self.next_word()
                    elif key == curses.KEY_BTAB:  # Shift-Tab
                        self.next_word(step=-1)
                    elif key == ord(" "):
                        self.toggle_cursor_direction()
                    elif 0 <= key < 256 and curses.ascii.isalpha(key):
                        self.type_letter(chr(key))
                    elif key == curses.KEY_UP:
                        self.arrow(-1, 0)
                    elif key == curses.KEY_DOWN:
                        self.arrow(1, 0)
                    elif key == curses.KEY_LEFT:
                        self.arrow(0, -1)
                    elif key == curses.KEY_RIGHT:
                        self.arrow(0, 1)
                    else:
                        continue

                    if key in (curses.KEY_BACKSPACE, 127, 8) or (0 <= key < 256 and curses.ascii.isalpha(key)):
                        self.save_progress(timer_seconds)

                    # Update display after handling input
                    # Congratulate once; after that, show clues again so the
                    # player can read the ones they never needed
                    if self.puzzle.is_solved and not was_solved:
                        message = "Congratulations!"
                    elif not self.puzzle.is_solved and self.puzzle.is_full and not nice_try_message_shown:
                        message = "Not quite, keep trying!"
                        nice_try_message_shown = True
                    elif self.puzzle.cursor_h:
                        message = str(self.puzzle.cursor_cell().across_clue)
                    else:
                        message = str(self.puzzle.cursor_cell().down_clue)
                    
                    self.puzzle.update_display(
                        stdscr,
                        message=message,
                        timer_seconds=timer_seconds,
                        full_update=False
                    )

                # Update display at least once per second
                if current_time - last_update_time >= 1:
                    self.puzzle.update_display(
                        stdscr,
                        message=message,
                        timer_seconds=timer_seconds,
                        full_update=False
                    )
                    last_update_time = current_time

        except KeyboardInterrupt:
            self.save_progress(timer_seconds)
            stdscr.clear()
            stdscr.refresh()
            return


def _ipuz_value(value):
    """An ipuz cell or solution entry may be a plain value or {"cell"/"value": ...}."""
    if isinstance(value, dict):
        return value.get("cell", value.get("value"))
    return value


def cells_from_ipuz(ipuz: dict) -> list[list[CrosswordCell]]:
    cells = []
    for i, row in enumerate(ipuz["puzzle"]):
        cells_row = []
        for j, cell in enumerate(row):
            solution = _ipuz_value(ipuz["solution"][i][j])
            if _ipuz_value(cell) in ("#", None) or solution in ("#", None):
                cells_row.append(CrosswordCell(i=i, j=j, solution=None, number=None, is_out_of_bounds=True))
                continue
            number = _ipuz_value(cell)
            style = cell.get("style", {}) if isinstance(cell, dict) else {}
            cells_row.append(CrosswordCell(
                i=i,
                j=j,
                solution=str(solution)[0].upper(),  # Rebus answers are reduced to their first letter
                number="" if number in (0, "0", "") else str(number),
                is_circled=style.get("shapebg") == "circle",
            ))
        cells.append(cells_row)
    return cells


def clues_from_ipuz(ipuz: dict) -> list[CrosswordClue]:
    clues = []
    for direction, direction_clues in ipuz["clues"].items():
        is_across = direction.split(":")[0].lower() == "across"
        for clue in direction_clues:
            if isinstance(clue, dict):
                number, text = clue.get("number"), clue.get("clue", "")
            else:
                number, text = clue[0], clue[1]
            clues.append(CrosswordClue(number=str(number), clue=text, is_across=is_across))
    return clues


def read_mini_puzzle_data(ipuz: dict):
    def get_clue(is_across: bool, number: str, clues: list[CrosswordClue]) -> str:
        for clue in clues:
            if clue.number == number and clue.is_across == is_across:
                return clue
        return None

    puzzle = cells_from_ipuz(ipuz)
    clues = clues_from_ipuz(ipuz)

    for across in (True, False):
        for word in word_runs(puzzle, across):
            i, j = word[0]
            clue = get_clue(across, puzzle[i][j].number, clues)
            for i, j in word:
                if across:
                    puzzle[i][j].across_clue = clue
                else:
                    puzzle[i][j].down_clue = clue

    return puzzle

def restore_progress(crossword: Crossword, progress: dict):
    for i, row in enumerate(progress.get("values", [])):
        for j, value in enumerate(row):
            if value.isalpha():
                crossword.set_cell(i, j, value)


def mini_scene(stdscr):
    stdscr.clear()
    record = load_mini_data(stdscr)
    if record is None:
        return placeholder_scene(stdscr, NO_PUZZLE_MESSAGE)
    crossword = Crossword(read_mini_puzzle_data(record["puzzle"]))
    restore_progress(crossword, record["progress"])
    controller = CrosswordController(crossword, record)

    controller.run(stdscr)