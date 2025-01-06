import curses
import random
from dataclasses import dataclass
from english_dictionary.scripts.read_pickle import get_dict

import utils

GRID_TEMPLATE = open("spellingbee/grid.txt").read()
GRID_WIDTH = len(GRID_TEMPLATE.split("\n")[0])
GRID_HEIGHT = len(GRID_TEMPLATE.split("\n"))
GRID_CHARACTER_COLOR_MAPPING = [
    (GRID_WIDTH*2 + 5, GRID_WIDTH*2 + 8, "yellow"),
    (GRID_WIDTH*3 + 4, GRID_WIDTH*3 + 9, "yellow"),
    (GRID_WIDTH*4 + 4, GRID_WIDTH*4 + 9, "yellow"),
]

dictionary = get_dict().keys()

def score_word(word: str) -> int:
    if len(word) < 4:
        return 0
    if len(word) == 4:
        return 1
    else:
        return len(word)


def get_rank(score: int, max_score: int) -> str:
    percentage = score / max_score
    if percentage < 0.02:
        return "Beginner"
    elif percentage < 0.05:
        return "Good Start"
    elif percentage < 0.08:
        return "Moving Up"
    elif percentage < 0.15:
        return "Good"
    elif percentage < 0.25:
        return "Solid"
    elif percentage < 0.40:
        return "Nice"
    elif percentage < 0.50:
        return "Great"
    elif percentage < 0.70:
        return "Amazing"
    elif percentage < 1:
        return "Genius"
    else:
        return "Queen Bee"


@dataclass
class GuessResult:
    word: str
    score: int
    is_valid: bool
    is_correct: bool
    message: str


class SpellingBeeGame:
    def __init__(self, letters:str , center_letter: chr, solution_words:list[str], score: int = 0):
        self.outer_letters: list[str] = list(set(letters.lower()) - set(center_letter.lower()))
        random.shuffle(self.outer_letters)
        self.letters = set(letters.lower()).union(set(center_letter.lower()))
        self.center_letter = center_letter.lower()
        self.solution_words = set(solution_words)
        self.score = score
        self.max_score = sum(score_word(word) for word in self.solution_words)
        self.message = "Welcome to Spelling Bee!"
        self.input_buffer = ""
        self.guesses = []

    @property
    def rank(self) -> str:
        return get_rank(self.score, self.max_score)

    def check_dictionary(self, word: str) -> bool:
        return word in dictionary
    
    def is_letter(self, letter: chr) -> bool:
        return letter.lower() in self.letters

    def is_center_letter(self, letter: chr) -> bool:
        return letter.lower() == self.center_letter

    def evaluate_guess(self, word: str) -> GuessResult:
        if len(word) < 4:
            return GuessResult(word, 0, False, False, "Too short")
        elif self.center_letter not in word:
            return GuessResult(word, 0, False, False, "Must contain the center letter")
        if word.lower() in self.guesses:
            return GuessResult(word, 0, False, False, "Already guessed")
        elif word in self.solution_words:
            return GuessResult(word, score_word(word), True, True, f"{word.upper()} is correct!")
        elif set(word) - self.letters:
            return GuessResult(word, 0, False, False, "Bad letters")
        elif self.check_dictionary(word):
            return GuessResult(word, 0, True, False, f"{word.upper()} is valid but not the solution")
        elif word not in self.solution_words:
            return GuessResult(word, 0, True, False, f"{word.upper()} Not a word")
        else:
            return GuessResult(word, 0, False, False, "An error occurred")

    def guess(self, word: str) -> GuessResult:
        result = self.evaluate_guess(word)
        self.guesses.append(result.word.lower())
        self.message = result.message
        if result.is_correct:
            self.score += result.score
        self.input_buffer = ""
        return result

    def update_display(self, stdscr, full_update: bool = False, guess_submitted: bool = False, reshuffle: bool = False):
        if full_update:
            stdscr.clear()
        
        vertical_offset = utils.vertical_buffer(GRID_HEIGHT, utils.display_rows(stdscr))
        horizontal_offset = utils.horizontal_buffer(GRID_WIDTH, utils.display_cols(stdscr))
        
        if full_update or reshuffle:
            grid = GRID_TEMPLATE
            random.shuffle(self.outer_letters)
            for i, letter in enumerate(self.outer_letters):
                grid = grid.replace(str(i+1), letter.upper())
            grid = grid.replace('7', self.center_letter.upper())
            grid_lines = grid.split("\n")
            for i in range(GRID_HEIGHT):
                for j in range(GRID_WIDTH):
                    chr_color = 'white'
                    for start, end, span_color in GRID_CHARACTER_COLOR_MAPPING:
                        p = i * GRID_WIDTH + j
                        if p >= start and p < end:
                            chr_color = span_color
                            break
                    stdscr.addstr(vertical_offset + i, horizontal_offset + j, grid_lines[i][j], utils.Palette.from_name(chr_color))

        current_input = utils.center_text(stdscr, self.input_buffer.upper())
        for i in range(len(current_input)):
            c = current_input[i]
            if not self.is_letter(c):
                color = utils.Palette.gray()
            elif self.is_center_letter(c):
                color = utils.Palette.yellow()
            else:
                color = utils.Palette.white()
            stdscr.addstr(vertical_offset + GRID_HEIGHT + 2, i, c, color)

        if full_update or guess_submitted:
            score_display = f"{self.score / self.max_score:.2%} / {self.rank} / {self.score}"
            stdscr.addstr(vertical_offset + GRID_HEIGHT + 4, 0, utils.center_text(stdscr, self.message))
            stdscr.addstr(vertical_offset + GRID_HEIGHT + 5, 0, utils.center_text(stdscr, score_display), utils.Palette.gray())
        
        stdscr.refresh()


def spellingbee_scene(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    stdscr.clear()

    game = SpellingBeeGame(
        letters="agilnt",
        center_letter="h",
        solution_words=[
            "halal",
            "hatha",
            "light",
            "night",
            "ninth",
            "thigh",
            "thing",
            "tight",
            "tilth",
            "hail",
            "hall",
            "halt",
            "hang",
            "hath",
            "high",
            "hill",
            "hilt",
            "hint",
            "lath",
            "nigh",
            "than",
            "that",
            "thin",
        ],
    )
    
    game.update_display(stdscr, full_update=True)

    try:
        while True:
            key = stdscr.getch()
            if key == curses.KEY_BACKSPACE or key == 127:
                game.input_buffer = game.input_buffer[:-1]
                game.update_display(stdscr)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                game.guess(game.input_buffer)
                game.update_display(stdscr, guess_submitted=True)
            elif key == ord('1'):
                game.update_display(stdscr, reshuffle=True)
            elif curses.ascii.isalpha(key):
                game.input_buffer += chr(key).lower()
                game.update_display(stdscr)
    except KeyboardInterrupt:
        stdscr.clear()
        stdscr.refresh()
        return
