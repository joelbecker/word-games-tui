"""Date-keyed puzzle storage.

Each puzzle is saved as ~/.wordgames/<game>/<YYYY-MM-DD>.json:

    {
        "game": "wordle",
        "date": "2026-11-18",
        "provider": "actions",
        "puzzle": {...},     # game-specific puzzle data from the provider
        "progress": {...}    # game-specific player progress; {} until started
    }
"""
import os
import json
import datetime

ROOT = os.path.expanduser("~/.wordgames")


def today() -> str:
    """The puzzle date to play: the device's local date."""
    return datetime.date.today().isoformat()


def puzzle_path(game: str, date: str) -> str:
    return os.path.join(ROOT, game, f"{date}.json")


def load(game: str, date: str):
    """Return the saved record for game/date, or None if there isn't a valid one."""
    try:
        with open(puzzle_path(game, date)) as f:
            record = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or "puzzle" not in record:
        return None
    record.setdefault("progress", {})
    return record


def save(record: dict) -> None:
    path = puzzle_path(record["game"], record["date"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(record, f)
    os.replace(tmp, path)  # Atomic, so a crash never leaves a half-written file


def save_progress(record: dict, progress: dict) -> None:
    record["progress"] = progress
    save(record)


def is_started(record) -> bool:
    return bool(record and record.get("progress"))
