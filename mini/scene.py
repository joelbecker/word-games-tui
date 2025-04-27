import utils
import curses
from time import sleep
from typing import Iterable, Callable
from mini.cycle import Cycle, prev, first, last

# TODO: Add puzzle state (not solution)
# TODO: Add cell input
# TODO: Add cell->word mappings
# TODO: Add clue display

class Crossword:

    def __init__(self, cells: list[list[str]], null_charcter_fn: Callable[[chr], str] = None) -> None:
        # definition
        self.solution = cells
        self.cells = [[c if c is None else " " for c in row] for row in cells]
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
                if cells[i][j] is not None
            ])
        )
        self.cursor_row, self.cursor_col = next(self.valid_cells)
        
        # options
        self.null_charcter_fn = null_charcter_fn

    def set_cell(self, i: int, j: int, c: str):
        if self.is_out_of_bounds(i, j):
            return False
        else:
            self.cells[i][j] = str(c).upper()
            return True

    def is_filled(self, i: int, j: int) -> bool:
        return not self.is_out_of_bounds(i, j) and self.cells[i][j].isalpha()

    def is_empty(self, i: int, j: int) -> bool:
        return not self.is_out_of_bounds(i, j) and not self.cells[i][j].isalpha()

    def is_cursor_cell(self, i: int, j: int) -> bool:
        return i == self.cursor_row and j == self.cursor_col

    def is_cursor_lane(self, i: int, j: int) -> bool:
        # TODO: Once cell->word mappings are defined, require that the cursor is on the same word
        return (
            i >= 0 and j >= 0 and i < self.rows and j < self.cols
        ) and (
            self.cells[i][j] is not None
        ) and (
            (self.cursor_h and i == self.cursor_row)
            or (not self.cursor_h and j == self.cursor_col)
        )

    def is_out_of_bounds(self, i: int, j: int) -> bool:
        return i < 0 or j < 0 or i >= self.rows or j >= self.cols or self.cells[i][j] is None

    def _check_coordinates(self, coords: list[tuple[int, int]], f: Callable[[int, int], bool], b: Callable[[Iterable[bool]], bool]):
        return b(f(i, j) for i, j in coords)
    
    def check_cursor_cells(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_cursor_cell, b)
    
    def check_cursor_lanes(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_cursor_lane, b)
    
    def check_out_of_bounds(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_out_of_bounds, b)

    def _color_character(self, i: int, j: int, c: str, rel_coords: list[tuple[int, int]]) -> tuple[chr, int]:
        coords = [(i + di, j + dj) for di, dj in rel_coords]
        is_white = c.isalpha() or self.check_out_of_bounds(coords)
        is_yellow = self.check_cursor_cells(coords)
        is_blue = self.check_cursor_lanes(coords)
        is_null = self.check_out_of_bounds(coords, all)
        
        if is_null and self.null_charcter_fn:
            return self.null_charcter_fn(c)
        
        if is_yellow:
            color = utils.Palette.yellow()
        elif is_blue:
            color = utils.Palette.blue()
        elif is_white:
            color = utils.Palette.white()
        else:
            color = utils.Palette.gray()

        return c, color

    def _character(self, i: int, j: int, is_hline: bool, is_vline: bool, is_center: bool) -> tuple[chr, int]:
        if is_center:
            value = self.cells[i][j] or " "
            return self._color_character(i, j, value, [(0, 0)])
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

    def update_display(self, stdscr, full_update: bool = False):
        width = self.cols * 4 + 1
        height = self.rows * 2 + 1
        hbuffer = utils.horizontal_buffer(width, utils.display_cols(stdscr))
        vbuffer = utils.vertical_buffer(height, utils.display_rows(stdscr))

        if full_update:
            stdscr.clear()
        
        # TODO: These partial updates are very broken. TBD whether it's needed for performance.
        y_start = 0 if full_update else self.cursor_row * 2 - 2
        x_start = 0 if full_update else self.cursor_col * 4 - 4
        y_end = height if full_update else y_start + 4
        x_end = width if full_update else x_start + 8

        for y in range(y_start, y_end):
            i = y // 2
            is_hline = y % 2 == 0
            for x in range(x_start, x_end):
                j = x // 4
                is_vline = x % 4 == 0
                is_center = x % 4 == 2 and y % 2 == 1
                try:
                    c, color = self._character(i, j, is_hline, is_vline, is_center)
                    stdscr.addstr(y + vbuffer, x + hbuffer, c, color)
                except Exception as e:
                    stdscr.addstr(y + vbuffer, x + hbuffer, "#")
                    raise e
        stdscr.refresh()
    

class CrosswordController:

    def __init__(self, puzzle: Crossword):
        self.puzzle = puzzle

    def _move_cursor(self, rows, cols):
        new_coords = (self.puzzle.cursor_row + rows, self.puzzle.cursor_col + cols)
        if not self.puzzle.is_out_of_bounds(*new_coords):
            self.puzzle.cursor_row, self.puzzle.cursor_col = new_coords
            self.puzzle.valid_cells.select(new_coords)
    
    def move_cursor_up(self):
        self._move_cursor(-1, 0)
    
    def move_cursor_down(self):
        self._move_cursor(1, 0)
    
    def move_cursor_left(self):
        self._move_cursor(0, -1)

    def move_cursor_right(self):
        self._move_cursor(0, 1)

    def cycle_cell(self, auto_skip: bool = True, reverse = False, condition: Callable[[int, int], bool] = None):
        def get_next_cell():
            
            next_cell_fn = prev if reverse else next
            crossover_fn = last if reverse else first

            next_cell = next_cell_fn(self.puzzle.valid_cells)

            if next_cell == crossover_fn(self.puzzle.valid_cells):
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
                
                # Recalculate next cell
                next_cell = next_cell_fn(self.puzzle.valid_cells)

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
        
        # Check there are cells to cycle through
        if not any([(i, j) != current_cell and condition(i, j) for i, j in self.puzzle.valid_cells]):
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
            next_lane_condition
        )

    def run(self, stdscr):
        self.puzzle.update_display(stdscr, full_update=True)
        try:
            while True:
                key = stdscr.getch()
                if key == curses.KEY_BACKSPACE or key == 127:
                    new_coords = self.cycle_cell(
                        auto_skip=False,
                        reverse=True,
                    )
                    self.puzzle.set_cell(
                        new_coords[0],
                        new_coords[1],
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
                    self.cycle_cell(auto_skip=False)
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
                self.puzzle.update_display(stdscr, full_update=True)
        except KeyboardInterrupt:
            stdscr.clear()
            stdscr.refresh()
            return
        
def mini_scene(stdscr):
    stdscr.clear()

    from mini.example_puzzles import puzzle_1, parse_puzzle
    puzzle = parse_puzzle(puzzle_1)
    crossword = Crossword(puzzle)
    controller = CrosswordController(crossword)

    controller.run(stdscr)