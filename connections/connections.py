import json
import curses
from random import randint
from textwrap import TextWrapper, wrap

from utils import justify
from scrape import PUZZLE_FILE

stdscr = curses.initscr()
curses.start_color()
curses.use_default_colors()
curses.curs_set(0)
curses.noecho()

for i in range(0, curses.COLORS-1):
        curses.init_pair(i + 1, i, -1)

ROWS, COLS = stdscr.getmaxyx()
ROWS = min(ROWS, 24)
COLS = min(COLS, 60)

# Define color pairs
PURPLE = curses.color_pair(170)
YELLOW = curses.color_pair(227)
GREEN = curses.color_pair(43)
BLUE = curses.color_pair(26)
WHITE = curses.color_pair(253)
GRAY = curses.color_pair(240)

class CategoryColor:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return self.name.lower()
    
    def __cmp__(self, other):
        return self.value - other.value

    @property
    def term_name(self):
        return 'magenta' if self.name == 'PURPLE' else str(self)

CategoryColor.YELLOW = CategoryColor("YELLOW", 0)
CategoryColor.GREEN = CategoryColor("GREEN", 1)
CategoryColor.BLUE = CategoryColor("BLUE", 2)
CategoryColor.PURPLE = CategoryColor("PURPLE", 3)


class Category:
    def __init__(self, color: CategoryColor, description: str, is_solved=False):
        self.color = color
        self.description = description
        self.is_solved = is_solved

    def solved(self):
        self.is_solved = True        

    def __eq__(self, value):
        return self.color == value.color
    

class Word:
    def __init__(self, word, category, is_selected=False):
        self.word = word
        self.category = category
        self.is_selected = is_selected

    @property
    def is_solved(self):
        return self.category.is_solved

    def selected(self, value=None):
        return Word(
            self.word,
            self.category,
            value if value is not None else not self.is_selected
        )
    
    def format(self, is_cursor=False, max_width=70):
        if self.is_solved:
            prefix = "| "
        elif is_cursor:
            prefix = "> "
        elif self.is_selected:
            prefix = "* "
        else:
            prefix = "  "
        
        w = TextWrapper(width=max_width)
        text = w.fill(prefix + self.word.upper())
        return text

    def solved_color(self):
        color = {
            "yellow": YELLOW,
            "green": GREEN,
            "blue": BLUE,
            "purple": PURPLE
        }.get(self.category.color.name.lower(), None)
        return color if self.is_solved else None

    def attributes(self):
        return curses.A_BOLD if self.is_selected else curses.A_NORMAL


def print_display(words, message="", cursor=0, full_update=True):
    column_width = COLS // 2
    vertical_padding = (ROWS - (len(words) + 4)) // 2
    description_column = [""] * len(words)
    if full_update:
        for i in range(4):
            index = i * 4
            category = words[index].category
            if category.is_solved:
                wrapped = wrap(text=category.description, width=column_width)
                for j in range(min(len(wrapped), 4)):
                    description_column[i*4+j] = wrapped[j]
    if full_update:
        stdscr.clear()

    start_index = 0 if full_update else max(0, cursor - 1)
    end_index = len(words) if full_update else min(len(words), cursor + 2)

    for i in range(start_index, end_index):  # Adjust to fit within the terminal window
        word = words[i]
        is_cursor = (i == cursor)
        solved_color_pair = word.solved_color()
        unsolved_color_pair = (WHITE | curses.A_REVERSE) if is_cursor else WHITE
        formatted_desc = justify(
            description_column[i],
            block=column_width,
            width=column_width,
            justify="right"
        ) + " "
        formatted_word = word.format(
            is_cursor=is_cursor,
            max_width=column_width
        ).upper()
        stdscr.addstr(
            i + 1 + vertical_padding,
            0,
            formatted_desc,
            (solved_color_pair or WHITE)
        )
        stdscr.addstr(
            i + 1 + vertical_padding,
            len(formatted_desc),
            formatted_word,
            (solved_color_pair or unsolved_color_pair) | word.attributes()
        )
    
    if full_update:
        stdscr.addstr(
            len(words) + 2 + vertical_padding,
            0,
            justify(message, block=column_width*2, width=column_width*2, justify="center"),
            WHITE
        )
        stdscr.addstr(
            len(words) + 3 + vertical_padding,
            0,
            justify(
                "[k]up [j]down [s]elect [g]uess [r]eshuffle [q]uit",
                block=column_width*2,
                width=column_width*2,
                justify="center"
            ),
            GRAY
        )
    
    stdscr.refresh()


class ConnectionsApp:
    def __init__(self, words, categories):
        self.words = words
        self.categories = categories
        self.guesses = 6
        self.cursor = 0
        self.order_seed = randint(4, 100)
        self.message = "Welcome to Connections!"
    
    def selected_words(self):
        return [word for word in self.words if word.is_selected]
    
    def score_guess(self):
        categories = [w.category for w in self.selected_words()]
        return max(categories.count(c) for c in categories)

    def up(self):
        unsolved = [i for i in range(len(self.words)) if not self.words[i].is_solved]
        if unsolved:
            self.cursor = max(
                0,
                self.cursor - 1,
                min(unsolved)
            )

    def down(self):
        unsolved = [i for i in range(len(self.words)) if not self.words[i].is_solved]
        if unsolved:
            self.cursor = max(
                min(
                    self.cursor + 1,
                    len(self.words) - 1
                ),
                min(unsolved),
            )

    def select(self):
        if self.words[self.cursor].is_selected or len(self.selected_words()) < 4:
            self.words[self.cursor] = self.words[self.cursor].selected()
    
    def guess(self):
        if len(self.selected_words()) == 4:
            score = self.score_guess()
            if score == 4:
                self.selected_words()[0].category.solved()
                self.sort()
            self.words = [w.selected(False) for w in self.words]
            self.guesses -= 1
        else:
            self.message = "Select 4 words to guess."
            return
        
        if all(w.is_solved for w in words):
            self.message = "You win!"
            self.update_display()
        elif self.guesses == 0:
            for c in self.categories:
                c.solved()
            self.message = "Out of guesses!"
            self.update_display()
            exit()
        elif score == 4:
            self.message = "Correct! Guesses left: {}".format(self.guesses)
        elif score == 3:
            self.message = "One away! Guesses left: {}".format(self.guesses)
        else:
            self.message = "Incorrect. Guesses left: {}".format(self.guesses)

    def shuffle(self):
        self.order_seed = randint(4, 100)
        self.sort()

    def sort(self):
        self.words = sorted(
            self.words, 
            key=lambda x: (
                x.category.color.value if x.is_solved
                else hash(x.word) % self.order_seed + 4
            )
        )
        self.cursor = max(
            self.cursor,
            next((i for i, word in enumerate(self.words) if not word.is_solved), 0)
        )

    def update_display(self, full_update=True):
        print_display(self.words, self.message, self.cursor, full_update=full_update)


def main(words, categories):
    state = ConnectionsApp(words, categories)
    state.sort()
    state.update_display(full_update=True)

    try:
        while True:
            key = chr(stdscr.getch())

            if key == 'k':
                state.up()
                state.update_display(full_update=False)
            elif key == 'j':
                state.down()
                state.update_display(full_update=False)
            elif key == 's':
                state.select()
                state.update_display(full_update=False)
            elif key == 'g':
                state.guess()
                state.update_display(full_update=True)
            elif key == 'r':
                state.shuffle()
                state.update_display(full_update=True)
            elif key == '1':
                state.message = "Cheat code activated."
                for w in state.words:
                    w.category.solved()
                state.sort()
                state.update_display(full_update=True)
            elif key == 'q':
                break
            else:
                continue
    finally:
        curses.endwin()

if __name__ == "__main__":
    try:
        with open(PUZZLE_FILE, 'r') as f:
            puzzles = json.load(f)
    except:
        print("Failed to load puzzle file.")
        exit()
    
    puzzle = puzzles[max(puzzles.keys())]
    categories, category_words = puzzle["categories"], puzzle["words"]
    categories = {
        "yellow": Category(CategoryColor.YELLOW, categories["yellow"]),
        "green": Category(CategoryColor.GREEN, categories["green"]),
        "blue": Category(CategoryColor.BLUE, categories["blue"]),
        "purple": Category(CategoryColor.PURPLE, categories["purple"]),
    }

    words = []
    for color, word_list in category_words.items():
        for word in word_list:
            words.append(Word(word, categories[color]))

    try:
        main(words, categories.values())
    finally:
        curses.endwin()
