import re
import os
import bs4
import json
import requests
import datetime

from loading_scene import run_loading_animation

SPELLINGBEE_FILENAME = os.path.expanduser("~/.wordgames/spellingbee.json")

def get_spellingbee_words():
    url = "https://www.sbsolver.com/answers"

    response = requests.get(url)

    center_letter = re.search(r"alt=\"center letter (\w)", response.text).group(1).lower()
    spellingbee_words = [w.lower() for w in re.findall(r"https://www.sbsolver.com/\w/(\w+)", response.text) if len(w) > 3 and w.isalpha()]

    soup = bs4.BeautifulSoup(response.text, "html.parser")
    date = soup.find("span", attrs={"class":"bee-date bee-current bee-loud bee-hover-inverse"}, recursive=True).a.text

    return center_letter, spellingbee_words, date

def update_spellingbee_data(spellingbee_words, center_letter):
    letters = set(center_letter)
    for word in spellingbee_words:
        letters.update(word)
    spellingbee_data = {
        "spellingbee_words": spellingbee_words,
        "letters": ''.join(letters),
        "center_letter": center_letter,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
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
    get_spellingbee_words()
    center_letter, spellingbee_words, date = run_loading_animation(stdscr, get_spellingbee_words, "Fetching SpellingBee words...", min_time=0.5)
    try:
        validate_spellingbee_words(spellingbee_words, center_letter)
    except ValueError as e:
        import pdb; pdb.set_trace()

    update_spellingbee_data(spellingbee_words, center_letter)

    with open(SPELLINGBEE_FILENAME, "r") as f:
        spellingbee_data = json.load(f)

    return spellingbee_data
