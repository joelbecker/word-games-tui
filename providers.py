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
import json
import logging
import urllib.error
import urllib.request

import store
import wgcrypt

LOG_FILE = os.path.join(store.ROOT, "providers.log")
CONFIG_FILE = os.path.join(store.ROOT, "config.json")


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


def load_config() -> dict:
    """Settings from ~/.wordgames/config.json, overridable by environment variables."""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except (OSError, ValueError):
        config = {}
    for key, env in (("actions_url", "WORDGAMES_ACTIONS_URL"), ("actions_password", "WORDGAMES_ACTIONS_PASSWORD")):
        if os.environ.get(env):
            config[key] = os.environ[env]
    return config


class ActionsProvider(Provider):
    """NYT puzzles published by word-game-actions as encrypted files at
    <actions_url>/<game>/<date>.json.enc."""
    name = "actions"

    def __init__(self, url: str, password: str):
        self.url = url.rstrip("/")
        self.password = password

    def fetch(self, game, date):
        url = f"{self.url}/{game}/{date}.json.enc"
        request = urllib.request.Request(url, headers={"User-Agent": "word-games-tui"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                blob = response.read()
        except urllib.error.HTTPError as e:
            raise ProviderError(f"{url}: HTTP {e.code}") from e
        return json.loads(wgcrypt.decrypt(blob, self.password))


def configured_providers() -> list:
    """Providers that only exist when set up in the config file."""
    config = load_config()
    if config.get("actions_url") and config.get("actions_password"):
        return [ActionsProvider(config["actions_url"], config["actions_password"])]
    return []


def providers_for(game: str) -> list:
    """The providers for a game, best first. Imports are lazy so that a
    provider's optional dependencies are only needed when it is used."""
    if game == "wordle":
        from wordle.scrape import MashableWordleProvider, RandomWordleProvider
        return configured_providers() + [MashableWordleProvider(), RandomWordleProvider()]
    if game == "connections":
        from connections.scrape import MashableConnectionsProvider
        return configured_providers() + [MashableConnectionsProvider()]
    if game == "spellingbee":
        from spellingbee.scrape import RandomSpellingBeeProvider
        return configured_providers() + [RandomSpellingBeeProvider()]
    if game == "mini":
        from mini.scrape import CrossShareProvider
        return configured_providers() + [CrossShareProvider()]
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
