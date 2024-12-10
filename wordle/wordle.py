import random
import os

# This file was written 100% on my Blackberry Classic. I plan to refactor
# it with the benefit of a real keyboard and editor, but I'm proud of this
# file for being a weird little hobby project. Adding this note so the context
# lives on in the git history.

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
NC="\033[0m"
WIDTH = 51

# load words
with open(os.path.expanduser("~/wordle/words.txt"), "r") as f:
    words = [s.strip() for s in f.readlines()]

with open(os.path.expanduser("~/wordle/answers.txt"), "r") as f:
    answers = [s.strip() for s in f.readlines()]
    
# initialize game state 
letters = "q w e r t y u i o p\na s d f g h j k l  \n  z x c v b n m      "
secret = random.choice(answers).strip()
guesses = []
clues = []
count = 0
message = ""

# game functions
def green(s):
    return GREEN + s + NC


def yellow(s):
    return YELLOW + s + NC


def guess(s, g):
    if len(g) != len(s):
        return "Guesses must be five letters"
    
    if g not in words:
        return "Not a valid word!"
    
    if g in guesses:
        return "Already guessed that word!"
     
    guesses.append(g)
    clue = ["_"] * 5
    sl = [c for c in s]
    for i in range(0, len(s)):
        if s[i] == g[i]:
            clue[i] = green(s[i].upper())
            sl.pop(sl.index(s[i]))
    for i in range(0, len(g)):
        if g[i] in sl and g[i] != s[i]:
            clue[i] = yellow(g[i])
            sl.pop(sl.index(g[i]))
    clue_string = "".join(clue)
    clues.append(clue_string)
    return ""


def print_banner(s):
    r = WIDTH - len(s) - 2
    leftr = r//2
    rightr = r - leftr
    print("-"*leftr + " " + s + " " + "-"*rightr)
    print()


def strip_ansi(s):
    return s.replace(YELLOW, "").replace(GREEN, "").replace(NC, "")


def print_center(s):
    reference = strip_ansi(s).strip()
    r = WIDTH - len(reference)
    leftr = r//2
    rightr = leftr
    print(" "*leftr + s.strip() + " "*rightr)


def clear_display():
    print("\033c")

     
def update_display(message):
    print_banner("WORDLE")
    for row in letters.split("\n"):
        print_center(row)
    print()
    print_banner("Guess " + str(count + 1) + "/6")
    for clue, guess in zip(clues, guesses):
        print_center(clue + " (" + guess + ")")
        print()
    if message:
        print_center(message)


# game loop
while count < 6:
    clear_display()
    update_display(message)
    message = ""
    
    # get guess
    g = input(" "*((WIDTH-6)//2)).strip().lower()
    
    # debug option check
    if g == "%":
        message = "debug: secret is " + secret
        continue
    
    # evaluate guess
    validation_error = guess(secret, g)
    if secret == g:
        clear_display()
        update_display("Congrats! You won in " + str(count+1) + " guesses.")
        exit()
    if validation_error:
        message = validation_error
    else:
        count += 1
        # update letter tracker
        for c in g:
            if c in secret:
                letters = letters.replace(c, c.upper())
            else:
                letters = letters.replace(c, "_")

    continue

print_center("You ran out of guesses. The word was: " + secret)
