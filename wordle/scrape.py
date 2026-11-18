import os
import random
import datetime

import providers
from loading_scene import run_loading_animation

WORDLE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_wordle_answer(date: str = None):
    import bs4
    import requests
    dt = datetime.date.fromisoformat(date) if date else datetime.date.today()
    month = dt.strftime("%B").lower()

    url = f"https://mashable.com/article/wordle-today-answer-{month}-{dt.day}-{dt.year}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = bs4.BeautifulSoup(response.text, "html.parser")

    wordle_answer = soup.find(name="strong", recursive=True).text.strip().replace(".", "").lower()

    assert len(wordle_answer) == 5, f"Wordle answer is not 5 letters, got {wordle_answer}"

    return wordle_answer


class MashableWordleProvider(providers.Provider):
    name = "mashable"

    def fetch(self, game, date):
        return {"answer": get_wordle_answer(date)}


class RandomWordleProvider(providers.Provider):
    """One random answer per day, seeded by the date."""
    name = "random"

    def fetch(self, game, date):
        with open(os.path.join(WORDLE_DIR, "answers.txt")) as f:
            answers = sorted(w.strip() for w in f if len(w.strip()) == 5)
        return {"answer": random.Random(f"wordle:{date}").choice(answers)}


def load_wordle_data(stdscr):
    stdscr.clear()
    return run_loading_animation(stdscr, lambda: providers.get_puzzle("wordle"), "Fetching Wordle answer...")
