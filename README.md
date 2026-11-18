# `word-games-tui`

`word-games-tui` is a lightweight implementation of several popular daily word games for the command line.

Currently implemented:
* Wordle
* Connections
* Spelling Bee
* Mini

Planned:
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
| Wordle | word-game-actions, Mashable, random (seeded by date) |
| Connections | word-game-actions, Mashable |
| Spelling Bee | word-game-actions, random (seeded by date) |
| Mini | word-game-actions, [CrossShare daily mini](https://crosshare.org/dailyminis) |

Mini puzzles are stored as [ipuz](http://www.ipuz.org/); `mini/puz.py`
converts Across Lite `.puz` files.

Puzzles and your progress are saved in `~/.wordgames/<game>/<date>.json`.
A puzzle you have started is kept for the day, even if a better provider
posts one later.

### word-game-actions

[word-game-actions](https://github.com/joelbecker/word-game-actions) fetches
the NYT puzzles on GitHub Actions and publishes them encrypted. To use it,
create `~/.wordgames/config.json`:

```json
{
  "actions_url": "https://raw.githubusercontent.com/joelbecker/word-game-actions/main/data",
  "actions_password": "<password>"
}
```

`WORDGAMES_ACTIONS_URL` and `WORDGAMES_ACTIONS_PASSWORD` environment
variables override the file.

Provider errors are logged to `~/.wordgames/providers.log`.
