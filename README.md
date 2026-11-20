# `word-games-tui`

`word-games-tui` is a lightweight implementation of several popular daily word games for the command line.

Currently implemented:
* Wordle
* Connections
* Spelling Bee
* Mini
* Strands

## Running

```sh
python main.py
```

The games run on the Python standard library. Optional packages
(`pip install -r requirements.txt`) enable the Mashable fallback puzzles
(`requests`, `beautifulsoup4`) and Spelling Bee's "not a word" check
(`english_dictionary`).

## Puzzles

Each game gets one puzzle per day from the first provider that has one:

| Game | Providers, best first |
|---|---|
| Wordle | NYT, Mashable, random (seeded by date) |
| Connections | NYT, Mashable |
| Spelling Bee | NYT, random (seeded by date) |
| Mini | NYT, [CrossShare daily mini](https://crosshare.org/dailyminis) |
| Strands | NYT |
| Parseword (scraper only; no game yet) | [parseword.com](https://www.parseword.com/daily) (today and yesterday only) |

NYT puzzles come from the data feeds the NYT game pages load (`nyt.py`).
They are not an official API, so if NYT changes them the games fall back
to the next provider until `nyt.py` is updated.

Mini puzzles are stored as [ipuz](http://www.ipuz.org/); `mini/puz.py`
converts Across Lite `.puz` files.

Puzzles and your progress are saved in `~/.wordgames/<game>/<date>.json`.
A puzzle you have started is kept for the day, even if a better provider
posts one later.

Provider errors are logged to `~/.wordgames/providers.log`.
