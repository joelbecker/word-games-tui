import os
import bs4
import json
import curses
import requests
import datetime

from loading_scene import run_loading_animation

WORDLE_FILENAME = os.path.expanduser("~/.wordgames/wordle.json")

def get_wordle_answer():
    month = datetime.datetime.now().strftime("%B")
    day = datetime.datetime.now().strftime("%d")
    year = datetime.datetime.now().strftime("%Y")

    url = f"https://mashable.com/article/wordle-today-answer-{month}-{day}-{year}"

    response = requests.get(url)

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    wordle_answer = soup.find(name="strong", recursive=True).text.strip().replace(".", "").lower()

    assert len(wordle_answer) == 5, f"Wordle answer is not 5 letters, got {wordle_answer}"

    return wordle_answer

def update_wordle_data(wordle_answer):
    wordle_data = {
        "wordle_answer": wordle_answer,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "guesses": [],
    }
    
    if not os.path.exists(os.path.dirname(WORDLE_FILENAME)):
        os.makedirs(os.path.dirname(WORDLE_FILENAME))
    
    if not os.path.exists(WORDLE_FILENAME):
        with open(WORDLE_FILENAME, "w") as f:
            json.dump(wordle_data, f)
    else:
        with open(WORDLE_FILENAME, "r") as f:
            data = json.load(f)
            if data["date"] != wordle_data["date"]:
                with open(WORDLE_FILENAME, "w") as f:
                    json.dump(wordle_data, f)

def load_wordle_data(stdscr):
    stdscr.clear()
    wordle_answer = run_loading_animation(stdscr, get_wordle_answer, "Fetching Wordle answer...")
    update_wordle_data(wordle_answer)

    with open(WORDLE_FILENAME, "r") as f:
        wordle_data = json.load(f)

    return wordle_data
