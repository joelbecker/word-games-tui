import os
import json
from datetime import datetime

import bs4
import requests


PUZZLE_FILE = os.path.expanduser('~/.wordgames/connections.json')


def parse_word_list(s):
    split_words = s.split(': ')[1].split(', ')
    return [word.lower() for word in split_words]


def is_word_category_list(ul):
    list_items = ul.find_all('li')
    if len(list_items) != 4:
        return False
    return all([len(parse_word_list(li.p.text)) == 4 for li in list_items])


def get_connections_puzzle(url):
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    
    html_lists = soup.find_all("ul")
    word_list = [l for l in html_lists if is_word_category_list(l)][0].find_all('li')

    category_names = {
        'yellow': word_list[0].p.strong.text,
        'green': word_list[1].p.strong.text,
        'blue': word_list[2].p.strong.text,
        'purple': word_list[3].p.strong.text
    }

    category_words = {
        'yellow': parse_word_list(word_list[0].p.text),
        'green': parse_word_list(word_list[1].p.text),
        'blue': parse_word_list(word_list[2].p.text),
        'purple': parse_word_list(word_list[3].p.text)
    }
    try:
        assert all(category_names.values()), "Each category must have a name."
        assert all(category_words.values()), "Each category must have words."
        for category, words in category_words.items():
            assert len(words) == 4, f"Category must have exactly 4 words, not {len(words)}. ({category}: {words})"
    except Exception as e:
        print(f"Error parsing puzzle for {url}: {e}")
        raise e
    
    return category_names, category_words

def fetch_latest_connections_puzzle(dt=None):
    if dt is None:
        dt = datetime.now()

    month = dt.strftime("%B").lower()
    day = int(dt.strftime("%d"))
    year = int(dt.strftime("%Y"))
    connections_url = 'https://mashable.com/article/nyt-connections-hint-answer-today-{}-{}'.format(
        month,
        day
    )
    if year >= 2025:
        connections_url += f'-{year}'

    scraped_categories, scraped_words = get_connections_puzzle(connections_url)
    
    puzzle_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'categories': scraped_categories,
        'words': scraped_words,
        'guesses': [],
        'is_finished': False,
    }

    if not os.path.exists(os.path.dirname(PUZZLE_FILE)):
        os.makedirs(os.path.dirname(PUZZLE_FILE))

    with open(PUZZLE_FILE, 'w') as f:
        json.dump(puzzle_data, f, indent=4)
    print("Puzzle data saved to {}".format(PUZZLE_FILE))
    
    return puzzle_data

if __name__ == "__main__":
    try:
        print(fetch_latest_connections_puzzle().keys())
    except Exception as e:
        print(f"Error: {e}")
        import pdb; pdb.post_mortem()
        exit()
