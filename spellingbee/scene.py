import curses
import random
from dataclasses import dataclass
from english_dictionary.scripts.read_pickle import get_dict

from spellingbee.scrape import load_spellingbee_data
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
        self.max_pangrams = sum(1 for word in self.solution_words if self.is_pangram(word))
        self.max_perfect_pangrams = sum(1 for word in self.solution_words if self.is_perfect_pangram(word))
        self.pangrams_found = 0
        self.perfect_pangrams_found = 0
        self.max_score = sum(self.score_word(word) for word in self.solution_words)
        self.message = f"Welcome to Spelling Bee!"
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

    def is_pangram(self, word: str) -> bool:
        return set(word.lower()) == self.letters
    
    def is_perfect_pangram(self, word: str) -> bool:
        return self.is_pangram(word) and len(word) == len(self.letters)

    def score_word(self, word: str) -> int:
        if len(word) < 4:
            return 0
        elif len(word) == 4:
            return 1
        elif self.is_pangram(word):
            return len(word) + 7
        else:
            return len(word)

    def evaluate_guess(self, word: str) -> GuessResult:
        if len(word) < 4:
            return GuessResult(word, 0, False, False, "Too short")
        elif self.center_letter not in word:
            return GuessResult(word, 0, False, False, "Must contain the center letter")
        if word.lower() in self.guesses:
            return GuessResult(word, 0, False, False, "Already guessed")
        elif word in self.solution_words:
            if self.is_perfect_pangram(word):
                self.perfect_pangrams_found += 1
                self.pangrams_found += 1
                correct_message = f"{word.upper()} is a perfect pangram!"
            elif self.is_pangram(word):
                self.pangrams_found += 1
                correct_message = f"{word.upper()} is a pangram!"
            else:
                correct_message = f"{word.upper()} is correct!"
            return GuessResult(word, self.score_word(word), True, True, correct_message)
        elif set(word) - self.letters:
            return GuessResult(word, 0, False, False, "Bad letters")
        elif self.check_dictionary(word):
            return GuessResult(word, 0, True, False, f"{word.upper()} is not in the solution")
        elif word not in self.solution_words:
            return GuessResult(word, 0, True, False, f"{word.upper()} is not a word")
        else:
            return GuessResult(word, 0, False, False, "An error occurred")

    def guess(self, word: str) -> GuessResult:
        result = self.evaluate_guess(word)
        if result.is_correct:
            self.guesses.append(result.word.lower())
        self.message = result.message
        if result.is_correct:
            self.score += result.score
        self.input_buffer = ""
        return word

    def update_display(self, stdscr, highlight: bool = False, full_update: bool = False, guess_submitted: bool = False, reshuffle: bool = False):
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
            score_display = f"{self.score / self.max_score:.2%} / {self.rank} / {self.score} pts"
            message_color = utils.Palette.yellow() if highlight else utils.Palette.white()
            stdscr.addstr(vertical_offset + GRID_HEIGHT + 4, 0, utils.center_text(stdscr, self.message), message_color)
            stdscr.addstr(vertical_offset + GRID_HEIGHT + 5, 0, utils.center_text(stdscr, score_display), utils.Palette.gray())
        
        stdscr.refresh()


def spellingbee_scene(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    stdscr.clear()

    spellingbee_data = load_spellingbee_data(stdscr)
    solution_words = spellingbee_data["spellingbee_words"]
    center_letter = spellingbee_data["center_letter"]
    letters = spellingbee_data["letters"]

    game = SpellingBeeGame(
        letters=letters,
        center_letter=center_letter,
        solution_words=solution_words,
    )
    
    game.update_display(stdscr, full_update=True)

    try:
        while True:
            key = stdscr.getch()
            if key == curses.KEY_BACKSPACE or key == 127:
                game.input_buffer = game.input_buffer[:-1]
                game.update_display(stdscr)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                word = game.guess(game.input_buffer)
                game.update_display(stdscr, guess_submitted=True, highlight=game.is_pangram(word))
            elif key == ord('1'):
                game.update_display(stdscr, reshuffle=True)
            elif key == ord('2'):
                game.message = f"Words: {len(game.guesses)}/{len(game.solution_words)}, Score: {game.score}/{game.max_score}"
                game.update_display(stdscr, guess_submitted=True)
            elif key == ord('3'):
                game.message = f"Pangrams: {game.pangrams_found}/{game.max_pangrams}, Perfect pangrams: {game.perfect_pangrams_found}/{game.max_perfect_pangrams}"
                game.update_display(stdscr, guess_submitted=True)
            elif curses.ascii.isalpha(key):
                game.input_buffer += chr(key).lower()
                game.update_display(stdscr)
    except KeyboardInterrupt:
        stdscr.clear()
        stdscr.refresh()
        return
