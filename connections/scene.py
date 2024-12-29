import curses.ascii
import os
import json
import curses
import threading
from random import randint
from datetime import datetime
from textwrap import TextWrapper, wrap

from utils import Palette, justify, display_cols, display_rows, vertical_buffer, horizontal_buffer
from connections.scrape import PUZZLE_FILE, fetch_latest_connections_puzzle

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
        self.flag: chr = None

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
        elif self.flag:
            prefix = "{} ".format(self.flag)
        else:
            prefix = "  "
        
        w = TextWrapper(width=max_width)
        text = w.fill(prefix + self.word.upper())
        return text

    def solved_color(self):
        color = {
            "yellow": Palette.yellow(),
            "green": Palette.green(),
            "blue": Palette.blue(),
            "purple": Palette.purple()
        }.get(self.category.color.name.lower(), None)
        return color if self.is_solved else None

    def attributes(self):
        if self.is_selected:
            return curses.A_BOLD
        elif self.flag:
            return curses.A_DIM
        else:
            return curses.A_NORMAL


class ConnectionsGame:
    def __init__(self, words, categories, stdscr):
        self.words: list[Word] = words
        self.categories: list[Category] = categories
        self.guesses: list[set[str]] = []
        self.mistakes_remaining = 4
        self.cursor = 0
        self.order_seed = randint(4, 100)
        self.message = "Welcome to Connections!"
        self.stdscr = stdscr
    
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
        guess = set(w.word for w in self.selected_words())
        if guess in self.guesses:
            self.message = "Already guessed."
            return
        if len(self.selected_words()) == 4:
            score = self.score_guess()
            if score == 4:
                self.selected_words()[0].category.solved()
                self.sort()
            self.words = [w.selected(False) for w in self.words]
            self.guesses.append(guess)
        else:
            self.message = "Select 4 words to guess."
            return
        
        if all(w.is_solved for w in self.words):
            self.message = "You win!"
            self.update_display()
        elif self.mistakes_remaining == 0:
            for c in self.categories:
                c.solved()
            self.message = "Out of guesses!"
            self.update_display()
        elif score == 4:
            self.message = "Correct! Mistakes remaining: {}".format(self.mistakes_remaining)
        elif score == 3:
            self.mistakes_remaining -= 1
            self.message = "One away! Mistakes remaining: {}".format(self.mistakes_remaining)
        else:
            self.mistakes_remaining -= 1
            self.message = "Incorrect. Mistakes remaining: {}".format(self.mistakes_remaining)

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

    @property
    def display_rows(self):
        return display_rows(self.stdscr)
    
    @property
    def display_cols(self):
        return display_cols(self.stdscr)

    def update_display(self, full_update=True):

        column_width = self.display_cols // 2
        vertical_padding = (self.display_rows - (len(self.words) + 5)) // 2
        description_column = [""] * len(self.words)
        if full_update:
            for i in range(4):
                index = i * 4
                category = self.words[index].category
                if category.is_solved:
                    wrapped = wrap(text=category.description, width=column_width)
                    for j in range(min(len(wrapped), 4)):
                        description_column[i*4+j] = wrapped[j]
        if full_update:
            self.stdscr.clear()

        start_index = 0 if full_update else max(0, self.cursor - 1)
        end_index = len(self.words) if full_update else min(len(self.words), self.cursor + 2)

        for i in range(start_index, end_index):  # Adjust to fit within the terminal window
            word = self.words[i]
            is_cursor = (i == self.cursor)
            solved_color_pair = word.solved_color()
            unsolved_color_pair = (Palette.white() | curses.A_REVERSE) if is_cursor else Palette.white()
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
            self.stdscr.addstr(
                i + 1 + vertical_padding,
                0,
                formatted_desc,
                (solved_color_pair or Palette.white())
            )
            self.stdscr.addstr(
                i + 1 + vertical_padding,
                len(formatted_desc),
                formatted_word,
                (solved_color_pair or unsolved_color_pair) | word.attributes()
            )
        
        if full_update:
            self.stdscr.addstr(
                len(self.words) + 2 + vertical_padding,
                0,
                justify(self.message, block=column_width*2, width=column_width*2, justify="center"),
                Palette.white()
            )

            controls1 = "[k]up [j]down [s]elect"
            controls2 = "[g]uess [r]eshuffle [q]uit"
            # controls3 = "[f]lag [c]lear"
            is_control_message_split = len(controls1) + len(controls2) > self.display_cols - 2
            self.stdscr.addstr(
                len(self.words) + 3 + vertical_padding,
                0,
                justify(
                    controls1 if is_control_message_split else "{} {}".format(controls1, controls2),
                    block=column_width*2,
                    width=column_width*2,
                    justify="center"
                ),
                Palette.gray()
            )
            if is_control_message_split:
                self.stdscr.addstr(
                    len(self.words) + 4 + vertical_padding,
                    0,
                    justify(
                        controls2,
                        block=column_width*2,
                        width=column_width*2,
                        justify="center"
                    ),
                    Palette.gray()
                )
        
        self.stdscr.refresh()


def connections_controller(words, categories, stdscr):
    state = ConnectionsGame(words, categories, stdscr)
    state.sort()
    state.update_display(full_update=True)
    while True:
        key = stdscr.getch()

        if key == ord('k'):
            state.up()
            state.update_display(full_update=False)
        elif key == ord('j'):
            state.down()
            state.update_display(full_update=False)
        elif key == ord('s'):
            state.select()
            state.update_display(full_update=False)
        elif key == ord('g'):
            state.guess()
            state.update_display(full_update=True)
        elif key == ord('r'):
            state.shuffle()
            state.update_display(full_update=True)
        elif key == ord('f'):
            state.words[state.cursor].flag = curses.ascii.ascii("?")
            state.sort()
            state.update_display()
        elif key == ord('c'):
            for w in state.words:
                w.flag = None
                w.is_selected = False
            state.update_display()
        elif key == ord('1'):
            state.message = "Cheat code activated."
            for w in state.words:
                w.category.solved()
            state.sort()
            state.update_display(full_update=True)
        elif key == ord('q'):
            break
        else:
            continue


def load_puzzle():
    try:
        with open(PUZZLE_FILE, 'r') as f:
            puzzle = json.load(f)
    except:
        print("Failed to load puzzle file.")
        exit()
    return puzzle

def fetch_puzzle():
    if not os.path.exists(PUZZLE_FILE):
        fetch_latest_connections_puzzle()
        puzzle = load_puzzle()
    else:
        puzzle = load_puzzle()
    
    if puzzle['date'] != datetime.now().strftime('%Y-%m-%d'):
        fetch_latest_connections_puzzle()
        puzzle = load_puzzle()

    return puzzle

def loading_animation(stdscr, fetch_puzzle_event):
        stdscr.nodelay(True)
        animation = ["|", "/", "-", "\\"]
        content = "Fetching puzzle... "
        idx = 0
        start_time = datetime.now()
        while True:
            vbuffer = vertical_buffer(1, display_rows(stdscr))
            hbuffer = horizontal_buffer(len(content) + 1, display_cols(stdscr))
            is_time_buffer_elapsed = (datetime.now() - start_time).total_seconds() >= 0.5
            stdscr.clear()
            stdscr.addstr(vbuffer, hbuffer, content + animation[idx % len(animation)])
            stdscr.refresh()
            idx += 1
            if not fetch_puzzle_event.is_set() and is_time_buffer_elapsed:
                break
            curses.napms(100)

def puzzle_loading_screen(stdscr):

    fetch_puzzle_event = threading.Event()
    puzzle = None

    def fetch_puzzle_in_background():
        nonlocal puzzle
        puzzle = fetch_puzzle()
        fetch_puzzle_event.clear()

    fetch_puzzle_event.set()
    fetch_thread = threading.Thread(target=fetch_puzzle_in_background)
    fetch_thread.start()

    loading_animation(stdscr, fetch_puzzle_event)
    fetch_thread.join()

    return puzzle

def connections_scene(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)
    
    for i in range(0, curses.COLORS-1):
        curses.init_pair(i + 1, i, -1)

    puzzle = puzzle_loading_screen(stdscr)

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

    connections_controller(words, categories.values(), stdscr)