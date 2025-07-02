import os
import json
from datetime import datetime
import logging


PUZZLE_FILE = os.path.expanduser('~/.wordgames/connections.json')
LOG_FILE = os.path.expanduser('~/.wordgames/connections.log')

# Ensure the directory exists before configuring logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def parse_word_list(s):
    # Occasionally, there are typos in the scraped data.
    # This fixes at least one puzzle, and doesn't seem to cause issues.
    s = s.replace('.', ',')
    
    split_words = s.split(': ')[1].split(', ')
    return [word.lower() for word in split_words]


def is_word_category_list(ul):
    list_items = ul.find_all('li')
    if len(list_items) != 4:
        return False
    
    parsed_word_lists = [parse_word_list(li.p.text) for li in list_items]
    word_counts = [len(l) for l in parsed_word_lists]
    is_valid = all([count == 4 for count in word_counts])
    any_valid = any([count == 4 for count in word_counts])
    if any_valid and not is_valid:
        logging.info(f"Raw HTML list: {ul}")
        logging.info(f"Possible false positive. Word counts: {word_counts} Word lists: {parsed_word_lists}")
    
    return is_valid


def get_connections_puzzle(url):
    from bs4 import BeautifulSoup
    from requests import get
    logging.info(f"Fetching puzzle from {url}")
    response = get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    html_lists = soup.find_all("ul")
    
    word_lists = [l for l in html_lists if is_word_category_list(l)]
    if not word_lists:
        logging.error("No valid word category lists found in the page")
        raise ValueError("Could not find word categories in the page")
    word_list = word_lists[0].find_all('li')

    category_names = {
        'yellow': word_list[0].p.strong.text.replace(":", ""),
        'green': word_list[1].p.strong.text.replace(":", ""),
        'blue': word_list[2].p.strong.text.replace(":", ""),
        'purple': word_list[3].p.strong.text.replace(":", "")
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
