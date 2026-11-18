"""Daily puzzles straight from NYT, using the data feeds the NYT game pages load.

Standard library only. These are not an official API and may change; when a
fetch fails, the game falls back to its next provider.
"""
import re
import json
import urllib.error
import urllib.request

import providers

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CONNECTIONS_COLORS = ["yellow", "green", "blue", "purple"]


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise providers.ProviderError(f"{url}: HTTP {e.code}") from e


def _check_date(actual: str, expected: str):
    if actual != expected:
        raise providers.ProviderError(f"Got the puzzle for {actual}, not {expected}")


def fetch_wordle(date: str) -> dict:
    data = json.loads(_get(f"https://www.nytimes.com/svc/wordle/v2/{date}.json"))
    _check_date(data["print_date"], date)
    return {"answer": data["solution"].lower()}


def fetch_connections(date: str) -> dict:
    data = json.loads(_get(f"https://www.nytimes.com/svc/connections/v2/{date}.json"))
    _check_date(data["print_date"], date)
    categories = data["categories"]  # Ordered easiest (yellow) to hardest (purple)
    if len(categories) != 4 or any(len(c["cards"]) != 4 for c in categories):
        raise providers.ProviderError("Expected 4 categories of 4 cards")
    return {
        "categories": {color: c["title"] for color, c in zip(CONNECTIONS_COLORS, categories)},
        "words": {
            color: [(card.get("content") or card["image_alt_text"]).lower() for card in c["cards"]]
            for color, c in zip(CONNECTIONS_COLORS, categories)
        },
    }


def fetch_spellingbee(date: str) -> dict:
    """The puzzle page embeds today's and yesterday's puzzles."""
    from spellingbee.scrape import make_puzzle
    html = _get("https://www.nytimes.com/puzzles/spelling-bee")
    match = re.search(r"window\.gameData\s*=\s*(\{.*?\})\s*</script>", html, re.S)
    if not match:
        raise providers.ProviderError("Could not find gameData on the Spelling Bee page")
    game_data = json.loads(match.group(1))
    for day in ("today", "yesterday"):
        data = game_data.get(day)
        if data and data["printDate"] == date:
            return make_puzzle(data["centerLetter"], data["answers"])
    raise providers.ProviderError(f"No Spelling Bee for {date} on the puzzle page")


def mini_to_ipuz(data: dict) -> dict:
    """Convert an NYT crossword JSON response to an ipuz crossword."""
    body = data["body"][0]
    width, height = body["dimensions"]["width"], body["dimensions"]["height"]
    puzzle, solution = [], []
    for row in range(height):
        puzzle_row, solution_row = [], []
        for col in range(width):
            cell = body["cells"][row * width + col]
            if not cell or "answer" not in cell:
                puzzle_row.append("#")
                solution_row.append("#")
                continue
            label = int(cell["label"]) if cell.get("label", "").isdigit() else 0
            if cell.get("type") in (2, 3):  # Circled or shaded
                puzzle_row.append({"cell": label, "style": {"shapebg": "circle"}})
            else:
                puzzle_row.append(label)
            solution_row.append(cell["answer"])
        puzzle.append(puzzle_row)
        solution.append(solution_row)

    clues = {"Across": [], "Down": []}
    for clue in body["clues"]:
        text = "".join(part.get("plain", "") for part in clue["text"])
        number = int(clue["label"]) if clue["label"].isdigit() else clue["label"]
        clues[clue["direction"]].append([number, text])

    return {
        "version": "http://ipuz.org/v2",
        "kind": ["http://ipuz.org/crossword#1"],
        "title": "The Mini",
        "author": ", ".join(data.get("constructors", [])),
        "copyright": f"© {data.get('copyright', '')} The New York Times",
        "date": data["publicationDate"],
        "dimensions": {"width": width, "height": height},
        "puzzle": puzzle,
        "solution": solution,
        "clues": clues,
    }


def fetch_mini(date: str) -> dict:
    """The Mini is only published for today and earlier."""
    data = json.loads(_get(f"https://www.nytimes.com/svc/crosswords/v6/puzzle/mini/{date}.json"))
    _check_date(data["publicationDate"], date)
    return mini_to_ipuz(data)


def fetch_strands(date: str) -> dict:
    data = json.loads(_get(f"https://www.nytimes.com/svc/strands/v2/{date}.json"))
    _check_date(data["printDate"], date)
    board = [row.upper() for row in data["startingBoard"]]
    answers = dict(data["themeCoords"])
    answers[data["spangram"]] = data["spangramCoords"]
    for word, coords in answers.items():
        if "".join(board[r][c] for r, c in coords) != word.upper():
            raise providers.ProviderError(f"Strands coordinates don't spell {word}")
    return {
        "clue": data["clue"],
        "board": board,
        "theme_words": {w.upper(): coords for w, coords in data["themeCoords"].items()},
        "spangram": data["spangram"].upper(),
        "spangram_coords": data["spangramCoords"],
        "valid_words": data.get("solutions", []),  # Non-theme words NYT accepts (for hints)
    }


FETCHERS = {
    "wordle": fetch_wordle,
    "connections": fetch_connections,
    "spellingbee": fetch_spellingbee,
    "mini": fetch_mini,
    "strands": fetch_strands,
}


class NytProvider(providers.Provider):
    name = "nyt"

    def fetch(self, game, date):
        return FETCHERS[game](date)
