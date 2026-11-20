"""Parseword daily puzzle from parseword.com. Standard library only.

The site's game loads each day's puzzle from /puzzles/<YYYY-MM-DD>.json. Only
today's and yesterday's files are public; other dates return 403.

The puzzle is stored as published, after checking the fields a game needs:

    puzzle       the clue phrase, e.g. "Turn, go bad at back of fridge"
    definition   the part of the phrase that defines the answer ("turn")
    solution     the answer ("rotate")
    mutations    the solving steps, in order. Each is
                 {"before": "go bad", "after": "rot",
                  "type": "substitution", "indicator": None}
                 where type is substitution, selection, charade (join),
                 anagram, reverse, cycle, deletion, container,
                 hidden_word, homophone or translation; the last step's
                 "after" is the solution
    synonyms     {word or phrase: [candidate replacements]}, including
                 decoys, as offered in the game
    wordTypes    {indicator word: [how it can act]}
    extraReplacements, wordDefinitions, linking, attribution,
    difficulty, startingScore: as published
"""
import json
import datetime

import providers
import store
from loading_scene import run_loading_animation

URL = "https://www.parseword.com/puzzles/{date}.json"


def _require(condition: bool, problem: str):
    if not condition:
        raise providers.ProviderError(f"Unexpected Parseword puzzle: {problem}")


def parse_puzzle(text: str) -> dict:
    try:
        data = json.loads(text)
    except ValueError:
        raise providers.ProviderError("Parseword puzzle is not JSON")
    _require(isinstance(data, dict), "not an object")
    for key in ("puzzle", "definition", "solution"):
        _require(isinstance(data.get(key), str) and data[key].strip(), f"missing {key}")
    _require(data["definition"].lower() in data["puzzle"].lower(), "definition is not in the phrase")
    mutations = data.get("mutations")
    _require(isinstance(mutations, list) and mutations, "no mutations")
    for step in mutations:
        _require(isinstance(step, dict) and all(isinstance(step.get(k), str) for k in ("before", "after", "type")),
                 f"bad mutation {step!r}")
    _require(mutations[-1]["after"].lower() == data["solution"].lower(), "the last step does not give the solution")
    _require(isinstance(data.get("synonyms", {}), dict), "bad synonyms")
    return data


def fetch_parseword(date: str) -> dict:
    from nyt import _get  # Plain urllib GET with a browser user agent
    return parse_puzzle(_get(URL.format(date=date)))


class ParsewordProvider(providers.Provider):
    name = "parseword"

    def fetch(self, game: str, date: str) -> dict:
        return fetch_parseword(date)


def todays_or_yesterdays_puzzle():
    """parseword.com releases each puzzle some hours after midnight Eastern,
    so until today's is out, play yesterday's."""
    record = providers.get_puzzle("parseword")
    if record is None:
        yesterday = datetime.date.fromisoformat(store.today()) - datetime.timedelta(days=1)
        record = providers.get_puzzle("parseword", yesterday.isoformat())
    return record


def load_parseword_data(stdscr):
    stdscr.clear()
    return run_loading_animation(stdscr, todays_or_yesterdays_puzzle, "Fetching Parseword puzzle...")
