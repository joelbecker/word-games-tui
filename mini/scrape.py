import re
import json
import datetime
import urllib.request

import providers
from loading_scene import run_loading_animation
from mini.puz import puz_to_ipuz

USER_AGENT = "word-games-tui"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read()


class CrossShareProvider(providers.Provider):
    """CrossShare's daily mini (https://crosshare.org/dailyminis), via its .puz download."""
    name = "crossshare"

    def puzzle_id(self, date: str) -> str:
        day = datetime.date.fromisoformat(date)
        html = _get(f"https://crosshare.org/dailyminis/{day.year}/{day.month}").decode("utf-8")
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        if not match:
            raise providers.ProviderError("Could not find the daily minis list")
        page = json.loads(match.group(1))["props"]["pageProps"]
        if (page.get("year"), page.get("month")) != (day.year, day.month - 1):  # Page months are 0-based
            raise providers.ProviderError(f"Daily minis page is for {page.get('year')}-{page.get('month')}")
        for entry in page["puzzles"]:
            if entry and entry[0] == day.day and entry[1]:
                return entry[1]["id"]
        raise providers.ProviderError(f"No CrossShare daily mini for {date}")

    def fetch(self, game, date):
        return puz_to_ipuz(_get(f"https://crosshare.org/api/puz/{self.puzzle_id(date)}"))


def load_mini_data(stdscr):
    stdscr.clear()
    return run_loading_animation(stdscr, lambda: providers.get_puzzle("mini"), "Fetching Mini crossword...")
