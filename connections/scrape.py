import re
import os
import sys
import json
import html
import html.parser
import calendar
import subprocess
from datetime import datetime


PUZZLE_FILE = os.path.expanduser('~/.wordgames/connections.json')


def is_word_list(s):
    return re.match(r': ([A-Z ]+(,)*){4}', s)


def parse_word_list(s):
    split_words = s.split(': ')[1].split(', ')
    return [word.lower() for word in split_words]


class ConnectionsParser(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_ul = False
            self.in_li = False
            self.ul_contents = []
            self.li_contents = []

        def handle_starttag(self, tag, attrs):
            if tag == 'ul':
                self.in_ul = True
                self.ul_contents.append([])

        def handle_endtag(self, tag):
            if tag == 'ul' and self.in_ul:
                self.in_ul = False

        def handle_data(self, data):
            if self.in_ul:
                self.ul_contents[-1].append(data)


def get_connections_puzzle(month: int, day: int):
    month_name = calendar.month_name[month].lower()
    connections_url = 'https://mashable.com/article/nyt-connections-hint-answer-today-{}-{}'.format(
        month_name,
        day
    )
    connections_html = subprocess.run(['curl', connections_url, '>', 'connections.html'], capture_output=True)
    
    parser = ConnectionsParser()
    parser.feed(connections_html.stdout.decode('utf-8'))

    html_lists = parser.ul_contents
    word_list = [html.unescape(l) for l in html_lists if any(is_word_list(s) for s in l)][0]

    # TODO: Parsing fails for Dec 6th puzzle, likely because of special characters in the category name

    categories = {
        'yellow': word_list[0],
        'green': word_list[2],
        'blue': word_list[4],
        'purple': word_list[6]
    }

    words= {
        'yellow': parse_word_list(word_list[1]),
        'green': parse_word_list(word_list[3]),
        'blue': parse_word_list(word_list[5]),
        'purple': parse_word_list(word_list[7])
    }

    assert all(categories.values()), "Each category must have a name."
    assert all(words.values()), "Each category must have words."
    assert all(len(v) == 4 for v in words.values()), "Each category must have exactly 4 words."

    return categories, words

if __name__ == "__main__":
    if len(sys.argv) != 4 and len(sys.argv) != 1:
        print("Usage: python scrape.py [<year> <month> <day>]")
        sys.exit(1)

    if len(sys.argv) == 4:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
    else:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
    scraped_categories, scraped_words = get_connections_puzzle(month, day)

    puzzle_data = {
        'date': '{}-{}-{}'.format(year, month, day),
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
    