from dataclasses import dataclass
import json
import time
import curses
import textwrap
from enum import StrEnum
from typing import Iterable, Callable

import utils
from mini.cycle import Cycle


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
    

class Crossword:
    def __init__(self, cells: list[list[CrosswordCell]]) -> None:
        # definition
        self.cells = cells
        self.rows = len(cells)
        self.cols = len(cells[0])
        
        # validation
        assert all(len(row) == self.cols for row in cells), "All rows must have the same length"
        
        # state
        self.cursor_h = True
        self.valid_cells = Cycle(
            sorted([
                (i, j) for i in range(self.rows)
                for j in range(self.cols)
                if not cells[i][j].is_out_of_bounds
            ])
        )
        self.cursor_row, self.cursor_col = next(self.valid_cells)
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

    def is_cursor_lane(self, i: int, j: int) -> bool:
        # TODO: Once cell->word mappings are defined, require that the cursor is on the same word
        return (
            i >= 0 and j >= 0 and i < self.rows and j < self.cols
        ) and (
            not self.cells[i][j].is_out_of_bounds
        ) and (
            (self.cursor_h and i == self.cursor_row)
            or (not self.cursor_h and j == self.cursor_col)
        )

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
            return self._color_character(i, j, cell.value if cell.is_filled else cell.number or " ", [(0, 0)])
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
        vbuffer = utils.vertical_buffer(y_end, utils.display_rows(stdscr))

        if full_update:
            stdscr.clear()

        minutes, seconds = divmod(timer_seconds, 60)
        timer_display = f"{int(minutes):02}:{int(seconds):02}"
        stdscr.addstr(1, (utils.display_cols(stdscr) - 5)//2, timer_display)

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
            text_width = x_end + hbuffer
            min_lines = 3
            wrapped_lines = textwrap.wrap(message, width=text_width)
            wrapped_lines.extend([" ".center(text_width)] * (min_lines - len(wrapped_lines)))
            for i, line in enumerate(wrapped_lines):
                centered_line = ' ' * (hbuffer // 2) + line.center(text_width, ' ')
                stdscr.addstr(
                    y_end + vbuffer + 1 + i,
                    0,
                    centered_line,
                    utils.Palette.white()
                )

        stdscr.refresh()
    

class CrosswordController:

    def __init__(self, puzzle: Crossword):
        self.puzzle = puzzle
        self.start_time = time.time()

    def _move_cursor(self, rows, cols):
        new_coords = (self.puzzle.cursor_row + rows, self.puzzle.cursor_col + cols)
        if not self.puzzle.is_out_of_bounds(*new_coords):
            self.puzzle.cursor_row, self.puzzle.cursor_col = new_coords
            self.puzzle.valid_cells.select(new_coords)
            return True
        else:
            return False
    
    def move_cursor_up(self):
        if self.puzzle.cursor_h:
            self.toggle_cursor_direction()
        return self._move_cursor(-1, 0)
    
    def move_cursor_down(self):
        if self.puzzle.cursor_h:
            self.toggle_cursor_direction()
        return self._move_cursor(1, 0)
    
    def move_cursor_left(self):
        if not self.puzzle.cursor_h:
            self.toggle_cursor_direction()
        return self._move_cursor(0, -1)

    def move_cursor_right(self):
        if not self.puzzle.cursor_h:
            self.toggle_cursor_direction()
        return self._move_cursor(0, 1)

    def toggle_cursor_direction(self):
        # Reset cycle direction
        if self.puzzle.cursor_h:
            sort_key = lambda cell: (cell[1], cell[0])
        else:
            sort_key = lambda cell: (cell[0], cell[1])
        
        self.puzzle.valid_cells = Cycle(
            sorted(
                self.puzzle.valid_cells,
                key=sort_key
            )
        )
        
        # Toggle direction
        self.puzzle.cursor_h = not self.puzzle.cursor_h

    def cycle_cell(self, auto_skip: bool = True, stop_at_end: bool = False, condition: Callable[[int, int], bool] = None):
        def get_next_cell():
            
            next_cell = next(self.puzzle.valid_cells)

            if auto_skip and next_cell == self.puzzle.valid_cells.first():
                
                self.toggle_cursor_direction()

                # Recalculate next cell
                next_cell = next(self.puzzle.valid_cells)

            if auto_skip:
                if self.puzzle.is_empty(*next_cell):
                    return next_cell
                else:
                    return get_next_cell()
            else:
                return next_cell
        
        if condition is None:
            condition = lambda i, j: (i, j) != (self.puzzle.cursor_row, self.puzzle.cursor_col)

        current_cell = (self.puzzle.cursor_row, self.puzzle.cursor_col)
        
        if stop_at_end:
            # Do nothing if cursor is at the end of the lane
            if self.puzzle.cursor_h and self.puzzle.is_out_of_bounds(self.puzzle.cursor_row, self.puzzle.cursor_col + 1):
                return current_cell
            elif not self.puzzle.cursor_h and self.puzzle.is_out_of_bounds(self.puzzle.cursor_row + 1, self.puzzle.cursor_col):
                return current_cell

        
        # Check there are cells to cycle through
        no_valid_cells = not any([(i, j) != current_cell and condition(i, j) for i, j in self.puzzle.valid_cells])
        no_empty_cells = not any([self.puzzle.is_empty(i, j) for i, j in self.puzzle.valid_cells])
        if auto_skip and (no_valid_cells or no_empty_cells):
            return self.cycle_cell(
                auto_skip=False,
                condition=lambda i, j: True
            )
        
        while True:
            next_cell = get_next_cell()

            if condition(*next_cell):
                self.puzzle.cursor_row, self.puzzle.cursor_col = next_cell
                return next_cell
            else:
                continue

    def cycle_lane(self, auto_skip: bool = True):
        if self.puzzle.cursor_h:
            next_lane_condition = lambda i, j: i != self.puzzle.cursor_row
        else:
            next_lane_condition = lambda i, j: j != self.puzzle.cursor_col
        return self.cycle_cell(
            auto_skip,
            condition=next_lane_condition,
        )

    def run(self, stdscr):
        stdscr.nodelay(True)  # Enable non-blocking input
        nice_try_message_shown = False
        last_update_time = time.time()
        message = str(self.puzzle.cursor_cell().across_clue)
        
        self.puzzle.update_display(
            stdscr,
            message=message,
            timer_seconds=0,
            full_update=True
        )

        try:
            while True:
                if not self.puzzle.is_solved:
                    current_time = time.time()
                    timer_seconds = current_time - self.start_time

                # Check for input
                key = stdscr.getch()
                if key != -1:  # Input detected
                    self.puzzle.prev_cursor_row = self.puzzle.cursor_row
                    self.puzzle.prev_cursor_col = self.puzzle.cursor_col
                    self.puzzle.prev_cursor_h = self.puzzle.cursor_h
                    self.puzzle.prev_message = message

                    if key == curses.KEY_BACKSPACE or key == 127:
                        if not self.puzzle.is_empty(self.puzzle.cursor_row, self.puzzle.cursor_col):
                            self.puzzle.set_cell(
                                self.puzzle.cursor_row,
                                self.puzzle.cursor_col,
                                " "
                            )
                        else:
                            if self.puzzle.cursor_h:
                                move_result = self.move_cursor_left()
                            else:
                                move_result = self.move_cursor_up()
                            if move_result:
                                self.puzzle.set_cell(
                                    self.puzzle.cursor_row,
                                    self.puzzle.cursor_col,
                                    " "
                                )
                    elif key == curses.KEY_ENTER or key in [10, 13]:
                        self.cycle_lane(auto_skip=True)
                    elif key == ord(" "):
                        self.cycle_cell(auto_skip=True)
                    elif curses.ascii.isalpha(key):
                        self.puzzle.set_cell(
                            self.puzzle.cursor_row,
                            self.puzzle.cursor_col,
                            chr(key)
                        )
                        self.cycle_cell(auto_skip=False, stop_at_end=True)
                    elif key == curses.KEY_UP:
                        self.move_cursor_up()
                    elif key == curses.KEY_DOWN:
                        self.move_cursor_down()
                    elif key == curses.KEY_LEFT:
                        self.move_cursor_left()
                    elif key == curses.KEY_RIGHT:
                        self.move_cursor_right()
                    else:
                        continue
                    
                    # Update display after handling input
                    if self.puzzle.is_full and not nice_try_message_shown:
                        message = "Not quite, keep trying!"
                        nice_try_message_shown = True
                    elif self.puzzle.is_solved:
                        message = "Congratulations!"
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
            stdscr.clear()
            stdscr.refresh()
            return
        

def read_mini_puzzle_data():
    from mini.scrape import MINI_PUZZLE_FILENAME, write_mini_puzzle_data
    
    def get_clue(is_across: bool, number: str, clues: list[CrosswordClue]) -> str:
        for clue in clues:
            if clue.number == number and clue.is_across == is_across:
                return clue
        return None
    
    
    write_mini_puzzle_data() # temp
    with open(MINI_PUZZLE_FILENAME, "r") as f:
        data = json.load(f)
    
    puzzle = [[CrosswordCell(**d) for d in row] for row in data["grid"]]

    clues = [CrosswordClue(
        number=clue["number"],
        clue=clue["clue"],
        is_across=clue["direction"].lower() == "across"
    ) for clue in data["clues"]]

    across_numbers = set([c.number for c in clues if c.is_across])
    down_numbers = set([c.number for c in clues if not c.is_across])

    for i in range(len(puzzle)):
        for j in range(len(puzzle[i])):
            cell = puzzle[i][j]
            if cell.is_out_of_bounds:
                continue
            if cell.number is not None and cell.number in across_numbers:
                last_number = cell.number
            clue = get_clue(True, last_number, clues)
            cell.across_clue = clue
            puzzle[i][j] = cell
            

    for j in range(len(puzzle[0])):
        for i in range(len(puzzle)):
            cell = puzzle[i][j]
            if cell.is_out_of_bounds:
                continue
            if cell.number is not None and cell.number in down_numbers:
                last_number = cell.number
            clue = get_clue(False, last_number, clues)
            cell.down_clue = clue
            puzzle[i][j] = cell

    return puzzle

def mini_scene(stdscr):
    stdscr.clear()
    puzzle = read_mini_puzzle_data()
    crossword = Crossword(puzzle)
    controller = CrosswordController(crossword)

    controller.run(stdscr)