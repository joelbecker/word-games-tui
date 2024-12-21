import termcolor
from typing import Iterable, Callable
from itertools import cycle
import sys
import termios
import tty

WHITE = "white"
GREY = "dark_grey"
BLUE = "blue"
YELLOW = "yellow"

class CrosswordGrid:

    def __init__(self, cells: list[list[str]], null_charcter_fn: Callable[[chr], str] = None) -> None:
        # definition
        self.cells = cells
        self.rows = len(cells)
        self.cols = len(cells[0])
        
        # validation
        assert all(len(row) == self.cols for row in cells), "All rows must have the same length"
        
        # state
        self.cursor_h = True
        self.valid_cells = cycle(
            sorted([
                (i, j) for i in range(self.rows)
                for j in range(self.cols)
                if cells[i][j] is not None
            ])
        )
        self.cursor_row, self.cursor_col = next(self.valid_cells)
        
        # options
        self.null_charcter_fn = null_charcter_fn

    def is_filled(self, i: int, j: int) -> bool:
        return not self.is_out_of_bounds(i, j) and self.cells[i][j]

    def is_cursor_cell(self, i: int, j: int) -> bool:
        return i == self.cursor_row and j == self.cursor_col

    def is_cursor_line(self, i: int, j: int) -> bool:
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
    
    def check_cursor_lines(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_cursor_line, b)
    
    def check_out_of_bounds(self, coords: list[tuple[int, int]], b: Callable[[Iterable[bool]], bool] = any) -> bool:
        return self._check_coordinates(coords, self.is_out_of_bounds, b)

    def _color_character(self, i: int, j: int, c: str, rel_coords: list[tuple[int, int]]) -> str:
        coords = [(i + di, j + dj) for di, dj in rel_coords]
        is_white = c.isalpha() or self.check_out_of_bounds(coords)
        is_yellow = self.check_cursor_cells(coords)
        is_blue = self.check_cursor_lines(coords)
        is_null = self.check_out_of_bounds(coords, all)
        
        if is_null and self.null_charcter_fn:
            return self.null_charcter_fn(c)
        
        if is_yellow:
            color = YELLOW
        elif is_blue:
            color = BLUE
        elif is_white:
            color = WHITE
        else:
            color = GREY

        return termcolor.colored(c, color)

    def _character(self, i: int, j: int, is_hline: bool, is_vline: bool, is_center: bool) -> str:
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

    def __str__(self):
        width = self.cols * 4 + 1
        height = self.rows * 2 + 1
        result = ""
        for y in range(height):
            i = y // 2
            is_hline = y % 2 == 0
            for x in range(width):
                j = x // 4
                is_vline = x % 4 == 0
                is_center = x % 4 == 2 and y % 2 == 1
                try:
                    result += self._character(i, j, is_hline, is_vline, is_center)
                except Exception as e:
                    result += "#"
                    raise e
            result += "\n"
        return result
    

class IndexController:

    def __init__(self, puzzle: CrosswordGrid):
        self.puzzle = puzzle

    def cycle_cell(self, auto_skip: bool = True, condition: Callable[[int, int], bool] = None):
        while True:
            next_cell = next(self.puzzle.valid_cells)
            
            if next_cell == min(self.puzzle.valid_cells):
                # Reset cycle direction
                if self.puzzle.cursor_h:
                    sort_key = lambda cell: (cell[0], cell[1])
                else:
                    sort_key = lambda cell: (cell[1], cell[0])
                self.puzzle.valid_cells = cycle(
                    sorted(
                        self.puzzle.valid_cells,
                        key=sort_key
                    )
                )
                
                # Toggle direction
                self.puzzle.cursor_h = not self.puzzle.cursor_h
                
                # Recalculate next cell
                next_cell = self.puzzle.valid_cells

            if (not auto_skip or not self.puzzle.is_filled(*next_cell)) and condition(*next_cell):
                self.puzzle.cursor_row, self.puzzle.cursor_col = next_cell
                return next_cell
            elif next_cell == (self.puzzle.cursor_row, self.puzzle.cursor_col):
                # If we have cycle through all the cells on auto_skip and none are empty
                return self.cycle_cell(
                    auto_skip=False,
                    condition=condition
                )
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

def parse_puzzle(s: str) -> list[list[str]]:
    return [[c if c.isalpha() else None for c in list(row)] for row in s.strip().split("\n")]

def compare_options(puzzle):
    puzzles = [
        str(CrosswordGrid(puzzle)).split("\n"),
        str(CrosswordGrid(puzzle, null_charcter_fn=lambda c: termcolor.colored(c, GREY))).split("\n"),
        str(CrosswordGrid(puzzle, null_charcter_fn=lambda c: termcolor.colored(c, "red"))).split("\n"),
        str(CrosswordGrid(puzzle, null_charcter_fn=lambda c: termcolor.colored(c if c == "+" else " "))).split("\n"),
    ]

    return "\n".join(["   ".join(t) for t in zip(*puzzles)])

def clear_display():
    print("\033c")

puzzle_1 = """
.ROSE
COUPS
OWNUP
DECRY
EDEN.
"""

puzzle_2 = """
...SIPS
..HELLA
.POLLEN
GOLFBAG
ALLIES.
SKEET..
PARS...
"""

puzzle_3 = """
..PTA
ISAAC
TORCH
TRITE
YES..
"""

puzzle_4 = """
PCS..
ALPS.
NERDS
.FISH
..GUY
"""

puzzle_5 = """
..MAS..
.SILKS.
HELLYES
ELK.DIE
REDWINE
.SUAVE.
..DYE..
"""

examples = [puzzle_1, puzzle_2, puzzle_3, puzzle_4, puzzle_5]

for i in range(len(examples)):
    clear_display()
    print(f"Example {i + 1}/{len(examples)}")
    print(
        CrosswordGrid(
            parse_puzzle(examples[i]),
            null_charcter_fn=lambda c: termcolor.colored(c, GREY)
        )
    )
    input()
