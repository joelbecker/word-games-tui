import re
import html
import html.parser
import subprocess

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


def get_connections_puzzle(month: str, day: int):

    connections_url = 'https://mashable.com/article/nyt-connections-hint-answer-today-{}-{}'.format(month, day)
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