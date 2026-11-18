"""Puzzle providers: where each game's daily puzzle comes from.

Each game has an ordered list of providers, best first. A provider returns
exactly one puzzle per date, either fetched from a daily source or generated
from a seed derived from the date.

Resolution rules (see get_puzzle):
* A puzzle the player has started is locked for that date.
* An unstarted puzzle from a fallback provider is replaced as soon as a
  better provider has a puzzle for that date (e.g. NYT posts after the
  random fallback was used).
"""
import os
import logging

import store

LOG_FILE = os.path.join(store.ROOT, "providers.log")


class ProviderError(Exception):
    """A provider could not supply a puzzle for the requested date."""


class Provider:
    name = "provider"

    def fetch(self, game: str, date: str) -> dict:
        """Return the puzzle data for game on date (YYYY-MM-DD), or raise."""
        raise NotImplementedError


def _logger():
    logger = logging.getLogger("wordgames.providers")
    if not logger.handlers:
        os.makedirs(store.ROOT, exist_ok=True)
        handler = logging.FileHandler(LOG_FILE)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def providers_for(game: str) -> list:
    """The providers for a game, best first. Imports are lazy so that a
    provider's optional dependencies are only needed when it is used."""
    from nyt import NytProvider
    if game == "wordle":
        from wordle.scrape import MashableWordleProvider, RandomWordleProvider
        return [NytProvider(), MashableWordleProvider(), RandomWordleProvider()]
    if game == "connections":
        from connections.scrape import MashableConnectionsProvider
        return [NytProvider(), MashableConnectionsProvider()]
    if game == "spellingbee":
        from spellingbee.scrape import RandomSpellingBeeProvider
        return [NytProvider(), RandomSpellingBeeProvider()]
    if game == "mini":
        from mini.scrape import CrossShareProvider
        return [NytProvider(), CrossShareProvider()]
    if game == "strands":
        return [NytProvider()]
    raise ValueError(f"Unknown game: {game}")


def get_puzzle(game: str, date: str = None, providers: list = None):
    """Return the stored record for game on date, fetching or upgrading it
    from providers as needed. Returns None if no provider has a puzzle."""
    date = date or store.today()
    providers = providers_for(game) if providers is None else providers
    names = [p.name for p in providers]
    record = store.load(game, date)

    if record is not None:
        if store.is_started(record) or record.get("provider") not in names:
            return record
        better = providers[:names.index(record["provider"])]
    else:
        better = providers

    logger = _logger()
    for provider in better:
        try:
            puzzle = provider.fetch(game, date)
        except Exception as e:  # A failing provider must never stop the game loading
            logger.warning(f"{game} {date}: provider {provider.name} failed: {e!r}")
            continue
        logger.info(f"{game} {date}: using provider {provider.name}")
        record = {
            "game": game,
            "date": date,
            "provider": provider.name,
            "puzzle": puzzle,
            "progress": {},
        }
        store.save(record)
        return record

    return record
