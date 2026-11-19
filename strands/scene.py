import curses
import curses.ascii

import store
import utils
from placeholder_scene import placeholder_scene, NO_PUZZLE_MESSAGE
from strands.scrape import load_strands_data

NEIGHBORS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
CELL_WIDTH = 4   # Letters are 4 columns apart, leaving room for "-" connectors
CELL_HEIGHT = 2  # and a line between rows for "|", "/" and "\" connectors


class StrandsGame:
    def __init__(self, puzzle: dict, found: list):
        self.board = [row.upper() for row in puzzle["board"]]
        self.rows, self.cols = len(self.board), len(self.board[0])
        self.clue = puzzle["clue"]
        self.spangram = puzzle["spangram"].upper()
        self.answers = {w.upper(): [tuple(c) for c in coords] for w, coords in puzzle["theme_words"].items()}
        self.answers[self.spangram] = [tuple(c) for c in puzzle["spangram_coords"]]
        self.found = [w for w in found if w in self.answers]
        self.buffer = ""
        self.placements = []    # Every path on the board that spells the buffer
        self.just_found = None  # Stays bold until the next search starts
        self.message = ""

    @property
    def is_complete(self) -> bool:
        return len(self.found) == len(self.answers)

    @property
    def used_cells(self) -> set:
        return {cell for word in self.found for cell in self.answers[word]}

    def find_placements(self, s: str) -> list:
        """All paths of adjacent (incl. diagonal), unused, non-repeating cells spelling s."""
        if not s:
            return []
        blocked = self.used_cells
        results = []

        def extend(path):
            if len(path) == len(s):
                results.append(list(path))
                return
            r, c = path[-1]
            for dr, dc in NEIGHBORS:
                cell = (r + dr, c + dc)
                if (0 <= cell[0] < self.rows and 0 <= cell[1] < self.cols
                        and cell not in blocked and cell not in path
                        and self.board[cell[0]][cell[1]] == s[len(path)]):
                    path.append(cell)
                    extend(path)
                    path.pop()

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == s[0] and (r, c) not in blocked:
                    extend([(r, c)])
        return results

    def valid_next_letters(self) -> set:
        return {
            letter for letter in set("".join(self.board))
            if self.find_placements(self.buffer + letter)
        }

    def type_letter(self, letter: str) -> bool:
        """Add a letter if the result can still be placed on the board."""
        letter = letter.upper()
        if self.is_complete or letter not in self.valid_next_letters():
            return False
        if not self.buffer:  # A new search
            self.just_found = None
            self.message = ""
        self.buffer += letter
        self.placements = self.find_placements(self.buffer)
        return True

    def backspace(self):
        self.buffer = self.buffer[:-1]
        self.placements = self.find_placements(self.buffer)

    def guess(self) -> bool:
        """Returns True if a new word was found."""
        word, self.buffer, self.placements = self.buffer, "", []
        if not word:
            return False
        if word in self.found:
            self.message = f"{word} already found"
        elif word in self.answers:
            self.found.append(word)
            self.just_found = word
            if self.is_complete:
                self.message = "You found all the theme words!"
            elif word == self.spangram:
                self.message = "SPANGRAM!"
            else:
                self.message = f"{word} is a theme word!"
            return True
        elif len(word) < 4:
            self.message = "Too short"
        else:
            self.message = f"{word} is not a theme word"
        return False

    # Display

    def _connectors(self, path, attr, connectors):
        """Add the connector characters between consecutive cells of a path."""
        for (r1, c1), (r2, c2) in zip(path, path[1:]):
            dr, dc = r2 - r1, c2 - c1
            y = min(r1, r2) * CELL_HEIGHT + (0 if dr == 0 else 1)
            if dc == 0:
                x, char = c1 * CELL_WIDTH, "|"
            elif dr == 0:
                # Fill the whole gap so the strand reads as a solid line
                x, char = min(c1, c2) * CELL_WIDTH + 1, "-" * (CELL_WIDTH - 1)
            else:
                x = min(c1, c2) * CELL_WIDTH + CELL_WIDTH // 2
                char = "\\" if dr * dc > 0 else "/"
            existing = connectors.get((y, x))
            if existing and existing[0] != char and {existing[0], char} == {"/", "\\"}:
                char = "X"  # Two placements cross here
            connectors[(y, x)] = (char, attr)

    def update_display(self, stdscr):
        stdscr.clear()
        grid_width = (self.cols - 1) * CELL_WIDTH + 1
        grid_height = (self.rows - 1) * CELL_HEIGHT + 1
        display_cols = utils.display_cols(stdscr)
        # Header (strands/mockup2.txt): input or message, progress, clue, then the grid
        top = utils.vertical_buffer(grid_height + 6, utils.display_rows(stdscr))
        left = utils.horizontal_buffer(grid_width, display_cols)
        grid_top = top + 6

        cell_attrs = {}
        connectors = {}
        for word in self.found:
            color = utils.Palette.yellow() if word == self.spangram else utils.Palette.red()
            for cell in self.answers[word]:
                cell_attrs[cell] = color
            self._connectors(self.answers[word], color, connectors)

        # Placements of the current string: highlighted letters, bold connectors
        for path in self.placements:
            for cell in path:
                cell_attrs[cell] = utils.Palette.white() | curses.A_BOLD | curses.A_REVERSE
            self._connectors(path, utils.Palette.white() | curses.A_BOLD, connectors)
        # A just-found word stays bold until the next search
        if self.just_found:
            path = self.answers[self.just_found]
            color = cell_attrs[path[0]]
            for cell in path:
                cell_attrs[cell] = color | curses.A_BOLD
            self._connectors(path, color | curses.A_BOLD, connectors)

        if self.buffer:
            stdscr.addstr(top, 0, utils.center_text(stdscr, self.buffer), utils.Palette.white() | curses.A_BOLD)
        else:
            stdscr.addstr(top, 0, utils.center_text(stdscr, self.message), utils.Palette.white())
        progress = f"{len(self.found)} of {len(self.answers)} theme words found"
        stdscr.addstr(top + 2, 0, utils.center_text(stdscr, progress), utils.Palette.gray())
        stdscr.addstr(top + 4, 0, utils.center_text(stdscr, self.clue), utils.Palette.white())

        for r in range(self.rows):
            for c in range(self.cols):
                attr = cell_attrs.get((r, c), utils.Palette.white())
                stdscr.addstr(grid_top + r * CELL_HEIGHT, left + c * CELL_WIDTH, self.board[r][c], attr)
        for (y, x), (char, attr) in connectors.items():
            stdscr.addstr(grid_top + y, left + x, char, attr)
        stdscr.refresh()


def strands_scene(stdscr):
    curses.curs_set(0)
    stdscr.clear()

    record = load_strands_data(stdscr)
    if record is None:
        return placeholder_scene(stdscr, NO_PUZZLE_MESSAGE)

    game = StrandsGame(record["puzzle"], record["progress"].get("found", []))
    if game.is_complete:
        game.message = "You found all the theme words!"
    game.update_display(stdscr)

    stdscr.timeout(-1)  # The loading screen leaves input non-blocking
    try:
        while True:
            key = stdscr.getch()
            if key in (curses.KEY_BACKSPACE, 127, 8):
                game.backspace()
            elif key in (curses.KEY_ENTER, 10, 13):
                if game.guess():
                    store.save_progress(record, {"found": game.found})
            elif 0 <= key < 256 and curses.ascii.isalpha(key):
                if not game.type_letter(chr(key)):
                    continue  # Not a valid next letter: ignore it
            else:
                continue
            game.update_display(stdscr)
    except KeyboardInterrupt:
        stdscr.clear()
        stdscr.refresh()
        return
