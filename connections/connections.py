from textwrap import TextWrapper, wrap
from termcolor import colored
from random import randint

from scrape import PUZZLE_FILE
from utils import clear_display, getch, justify, print_center
from datetime import datetime
import json


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
    
    def formatted(self, is_cursor=False, max_width=70):
        if self.is_solved:
            prefix = "| "
        elif self.is_selected:
            prefix = "* "
        elif is_cursor:
            prefix = "> "
        else:
            prefix = "  "
        
        w = TextWrapper(width=max_width)
        text = w.fill(prefix + self.word.upper())
        on_color = "on_dark_grey" if is_cursor and not self.is_solved else None
        attrs = ["bold"] if self.is_selected else None

        return colored(
            text,
            color=self.category.color.term_name if self.is_solved else None,
            on_color=on_color,
            attrs=attrs
        )


def print_display(words, message = "", cursor=0):
    
    column_width = 25
    description_column = [""] * len(words)
    for i in range(4):
        index = i * 4
        category = words[index].category
        if category.is_solved:
            wrapped = wrap(text=category.description, width=column_width)
            for j in range(min(len(wrapped), 4)):
                description_column[i*4+j] = wrapped[j]

    clear_display()

    for i in range(len(words)):
        formatted_desc = colored(description_column[i], color=words[i].category.color.term_name)
        formatted_word = words[i].formatted(is_cursor=(i == cursor), max_width=column_width)
        
        print_center(
            justify(formatted_desc, block=column_width, width=column_width, justify="right")
            + " "
            + justify(formatted_word, block=column_width, width=column_width, justify="left"),
            block=51,
            width=51,
        )
    print()
    print_center(message)
    print()
    print_center("k-up j-down s-select g-guess r-shuffle q-quit")
    print()


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
        self.cursor = max(
            0,
            self.cursor - 1,
            min(i for i in range(len(self.words)) if not self.words[i].is_solved)
        )

    def down(self):
        self.cursor = min(
            max(i for i in range(len(self.words)) if not self.words[i].is_solved),
            self.cursor + 1,
            len(self.words) - 1
        )

    def select(self):
        if self.words[self.cursor].is_selected or len(self.selected_words()) < 4:
            self.words[self.cursor] = self.words[self.cursor].selected()
    
    def guess(self):
        if len(self.selected_words()) == 4:
            score = self.score_guess()
            if score == 4:
                self.selected_words()[0].category.solved()
            self.words = [w.selected(False) for w in self.words]
            self.guesses -= 1
        else:
            self.message = "Select 4 words to guess."
            return
        
        if all(w.is_solved for w in words):
            self.message = "You win!"
            self.update_display()
            exit()
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

    def update_display(self):
        self.words = sorted(
            self.words, 
            key=lambda x: (
                x.category.color.value if x.is_solved
                else hash(x.word) % self.order_seed + 4
            )
        )
        print_display(self.words, self.message, self.cursor)


def main(words, categories):
    state = ConnectionsApp(words, categories)
    state.update_display()

    while True:
        key = getch()

        if key == 'k':
            state.up()
        elif key == 'j':
            state.down()
        elif key == 's':
            state.select()
        elif key == 'g':
            state.guess()
        elif key == 'r':
            state.shuffle()
        elif key == 'q':
            exit()
        else:
            continue

        state.update_display()

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

    main(words, categories.values())
