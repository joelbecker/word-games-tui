import json
import os
import random
import curses
import curses.ascii

import utils
from wordle.scrape import WORDLE_FILENAME, load_wordle_data

# load words
with open(os.path.expanduser("wordle/words.txt"), "r") as f:
    WORD_LIST = [s.strip() for s in f.readlines()]
    
KEYBOARD = "q w e r t y u i o p\na s d f g h j k l  \n  z x c v b n m      ".split("\n")


class WordleGame:
    def __init__(self, secret, guesses):
        self.secret = secret.lower()
        self.guesses = guesses
        self.count = len(guesses)
        self.message = "Welcome to Wordle!"
        self.green_letters = set()
        self.yellow_letters = set()
        self.guessed_letters = set()

    def is_win(self):
        return len(self.guesses) > 0 and self.guesses[-1] == self.secret

    def is_lose(self):
        return self.count == 6

    def check_invalid_guess(self, guess):
        if len(guess) != 5:
            return "Guesses must be five letters"
        
        if guess not in WORD_LIST:
            return "Not a valid word!"
        
        if guess in self.guesses:
            return "Already guessed that word!"
        
        return ""
    
    def generate_clue(self, secret: str, guess: str) -> list[tuple[chr, int]]:
        clue = [(c, utils.Palette.gray()) for c in guess]
        sl = [c for c in secret]
        for i in range(0, len(secret)):
            self.guessed_letters.add(guess[i])
            if secret[i] == guess[i]:
                clue[i] = (guess[i], utils.Palette.green())
                self.green_letters.add(secret[i])
                sl.pop(sl.index(secret[i]))
        for i in range(0, len(guess)):
            if guess[i] in sl and guess[i] != secret[i]:
                clue[i] = (guess[i], utils.Palette.yellow())
                sl.pop(sl.index(guess[i]))
                self.yellow_letters.add(guess[i])
        
        return clue
    
    def update_display(self, stdscr, buffer, full_update=False):
        hbuffer = utils.horizontal_buffer(5, utils.display_cols(stdscr))
        vbuffer = utils.vertical_buffer(17, utils.display_rows(stdscr))
        hbuffer_keyboard = utils.horizontal_buffer(len(KEYBOARD[0]), utils.display_cols(stdscr))
        
        if full_update:
            stdscr.clear()
        
        if full_update:
            for i in range(0, self.count):
                clue = self.generate_clue(self.secret, self.guesses[i])
                for idx in range(len(clue)):
                    letter, color = clue[idx]
                    stdscr.addstr(vbuffer+i*2, hbuffer+idx, letter.upper(), color)
        
        for i in range(5):
            if i < len(buffer):
                stdscr.addstr(vbuffer+self.count*2, hbuffer+i, buffer[i].upper(), utils.Palette.white())
            else:
                stdscr.addstr(vbuffer+self.count*2, hbuffer+i, " ", utils.Palette.white())

        for i in range(len(KEYBOARD)):
            for j in range(len(KEYBOARD[i])):
                if KEYBOARD[i][j] in self.green_letters:
                    color = utils.Palette.green()
                elif KEYBOARD[i][j] in self.yellow_letters:
                    color = utils.Palette.yellow()
                elif KEYBOARD[i][j] in self.guessed_letters:
                    color = utils.Palette.gray()
                else:
                    color = utils.Palette.white()
                stdscr.addstr(vbuffer+12+i, hbuffer_keyboard+j, KEYBOARD[i][j].upper(), color)

        if full_update:
            stdscr.addstr(vbuffer+16, 0, utils.justify(self.message, len(self.message), utils.display_cols(stdscr)), utils.Palette.white())
        
        stdscr.refresh()

def wordle_scene(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    stdscr.clear()

    wordle_data = load_wordle_data(stdscr)

    game = WordleGame(wordle_data["wordle_answer"], wordle_data["guesses"])
    
    game.update_display(stdscr, "", full_update=True)

    input_buffer = ""

    while True:
        key = stdscr.getch()
        if not game.is_win() and not game.is_lose():
            if key == curses.KEY_BACKSPACE or key == 127:
                input_buffer = input_buffer[:-1]
                game.update_display(stdscr, input_buffer, full_update=True)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if game.check_invalid_guess(input_buffer):
                    game.message = game.check_invalid_guess(input_buffer)
                    game.update_display(stdscr, input_buffer, full_update=True)
                else:
                    game.guesses.append(input_buffer)
                    game.count += 1
                    input_buffer = ""
                    if game.is_win():
                        game.message = "You win!"
                        game.update_display(stdscr, "", full_update=True)
                    elif game.is_lose():
                        game.message = "Out of guesses! Answer was: " + game.secret.upper()
                        game.update_display(stdscr, "", full_update=True)
                    else:
                        game.message = f"Incorrect. {6 - game.count} guesses remaining."
                        game.update_display(stdscr, "", full_update=True)
            elif curses.ascii.isalpha(key) and len(input_buffer) < 5:
                input_buffer += chr(key).lower()
                game.update_display(stdscr, input_buffer, full_update=False)
            elif key == ord('1'):
                import pdb; pdb.set_trace()
        
        # Exit on Esc
        if key == 27:
            stdscr.nodelay(True)
            n = stdscr.getch()
            go = n == -1
            stdscr.nodelay(False)
            if go:
                exit()
