from textwrap import TextWrapper, wrap
from termcolor import colored
from random import randint
from enum import IntEnum

from scrape import get_connections_puzzle
from utils import clear_display, getch, justify, print_center
from datetime import datetime

# TODO: Remove dependency on enum and dataclass for Python 3.2 compatibility

class CategoryColor(IntEnum):
    YELLOW = 0
    GREEN = 1
    BLUE = 2
    PURPLE = 3

    def __str__(self):
        return self.name.lower()
    
    @property
    def term_name(self):
        return 'magenta' if self.name == 'PURPLE' else str(self)


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
        
        w = TextWrapper(width=max_width, max_lines=1, placeholder="...")
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
            wrapped = wrap(text=category.description, width=column_width, max_lines=4)
            for j in range(len(wrapped)):
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
            self.message = f"Correct! Guesses left: {self.guesses}"
        elif score == 3:
            self.message = f"One away! Guesses left: {self.guesses}"
        else:
            self.message = f"Incorrect. Guesses left: {self.guesses}"

    def shuffle(self):
        self.order_seed = randint(4, 100)

    def update_display(self):
        self.words = sorted(
            self.words, 
            key=lambda x: (
                x.category.color if x.is_solved
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
    month = datetime.now().strftime("%B").lower()
    day = datetime.now().day-9

    scraped_categories, scraped_words = get_connections_puzzle(month, day)
    
    categories = {
        "yellow": Category(CategoryColor.YELLOW, scraped_categories["yellow"]),
        "green": Category(CategoryColor.GREEN, scraped_categories["green"]),
        "blue": Category(CategoryColor.BLUE, scraped_categories["blue"]),
        "purple": Category(CategoryColor.PURPLE, scraped_categories["purple"]),
    }

    words = []
    for color, word_list in scraped_words.items():
        for word in word_list:
            words.append(Word(word, categories[color]))

    main(words, categories.values())
