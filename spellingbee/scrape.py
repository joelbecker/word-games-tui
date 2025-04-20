import re
import os
import json
import logging

from loading_scene import run_loading_animation
from utils import scrape_with_selenium

SPELLINGBEE_FILENAME = os.path.expanduser("~/.wordgames/spellingbee.json")
SPELLINGBEE_LOG = os.path.expanduser("~/.wordgames/spellingbee.log")

# Set up logging
logging.basicConfig(
    filename=SPELLINGBEE_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def is_valid_spellingbee_word(word):
    is_valid_format = len(word) > 3 and word.isalpha() 

    # Scraped page contains non-words like cdEklow that need to be removed
    # These are always the 7 letters with one emphasized by case
    is_non_word = word != word.lower() and len(set(word)) == 7
    if not is_non_word:
        logging.info(f"Removed non-word: {word}")

    return is_valid_format and not is_non_word

def get_spellingbee_words():
    import bs4
    url = "https://www.nytimes.com/puzzles/spelling-bee"

    # Use scrape_with_selenium to fetch the page source
    html = scrape_with_selenium(url)
    # Temporary to avoid rate limiting
    # with open(os.path.expanduser("~/Downloads/spellingbee.html"), "r") as f:
    #     html = f.read()

    soup = bs4.BeautifulSoup(html, "html.parser")
    game_data_raw = soup.find(
        "div",
        attrs={
            "id": "js-hook-pz-moment__game"
        },
        recursive=True
    ).script.text.replace("window.gameData = ", "").replace(";", "")
    
    game_data = json.loads(game_data_raw)

    date = game_data["today"]["printDate"]
    center_letter = game_data["today"]["centerLetter"]
    spellingbee_words = game_data["today"]["answers"]

    return center_letter, spellingbee_words, date

def update_spellingbee_data(spellingbee_words, center_letter, date):
    letters = set(center_letter)
    for word in spellingbee_words:
        letters.update(word)
    spellingbee_data = {
        "spellingbee_words": spellingbee_words,
        "letters": ''.join(letters),
        "center_letter": center_letter,
        "date": date,
        "guesses": [],
    }
    
    if not os.path.exists(os.path.dirname(SPELLINGBEE_FILENAME)):
        os.makedirs(os.path.dirname(SPELLINGBEE_FILENAME))
    
    if not os.path.exists(SPELLINGBEE_FILENAME):
        with open(SPELLINGBEE_FILENAME, "w") as f:
            json.dump(spellingbee_data, f)
    else:
        with open(SPELLINGBEE_FILENAME, "r") as f:
            try:
                data = json.load(f)
                if data["date"] != spellingbee_data["date"]:
                    with open(SPELLINGBEE_FILENAME, "w") as g:
                        json.dump(spellingbee_data, g)
            except json.JSONDecodeError:
                with open(SPELLINGBEE_FILENAME, "w") as g:
                    json.dump(spellingbee_data, g)

def validate_spellingbee_words(spellingbee_words, center_letter):
    letters = set(center_letter)
    for word in spellingbee_words:
        if center_letter not in word:
            raise ValueError("solution contains word without center letter: {}".format(word))
        letters.update(word)
    if len(letters) != 7:
        raise ValueError("solution contains wrong number of letters: {}".format(letters))

def load_spellingbee_data(stdscr):
    stdscr.clear()

    center_letter, spellingbee_words, date = run_loading_animation(stdscr, get_spellingbee_words, "Fetching SpellingBee words...", min_time=0.5)
    try:
        validate_spellingbee_words(spellingbee_words, center_letter)
    except ValueError as e:
        import pdb; pdb.set_trace()

    update_spellingbee_data(spellingbee_words, center_letter, date)

    with open(SPELLINGBEE_FILENAME, "r") as f:
        spellingbee_data = json.load(f)

    return spellingbee_data
