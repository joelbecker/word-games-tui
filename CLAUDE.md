# word-games-tui

A curses app for playing daily word games (Wordle, Connections, Mini, Strands,
Spelling Bee, Parseword) in a terminal. The real target is a **BlackBerry Key2
running Termux (Android 8)** with a physical keyboard, so "works on my Mac" is
not the end of the story.

## How to work here

- **Dependency-light.** Use the Python standard library and plain sh. A new
  package needs a very good reason. `requests`, `beautifulsoup4` and
  `english_dictionary` are optional extras and the games must run without them.
- **If it ain't broke, don't fix it.** Keep changes targeted to what was asked.
  Don't refactor or "tidy" neighbouring code along the way.
- **New UI goes through the user.** The user designs layouts as mockups
  (`<game>/mockup*.txt`). Follow the mockup exactly. If one is ambiguous or
  seems wrong, ask instead of improvising. Don't invent new screens or layouts.
- **Commit directly to `main` and push to `origin/main`** as you go, without
  asking. The user pulls the latest version onto the BlackBerry, so every commit
  should be on `origin/main`. Don't create branches unless asked.
- **Linear:** the project is "word-games-tui" (team "Joel Becker Personal", key
  `J`). Move a ticket to In Progress when you start it and to Done when it works
  locally. Done means working locally; the user tests on the BlackBerry
  separately.
- **Verify in the real app.** Before calling something done, run it in a pty
  (see Testing) and look at the screen, not only at the logic.

## Running

```sh
just play    # python main.py
just reset   # delete saved puzzles and progress (or: just reset <game>); keeps settings
```

## Termux / BlackBerry constraints

- Every screen is laid out in a box of at most **60 columns x 24 rows**,
  centred on the terminal by `utils.SafeWindow` (scenes draw in box
  coordinates; `getmaxyx`, `display_cols` and `display_rows` give the box size).
  Scenes centre their whole block in the box. Use `utils.fit_rows` so blank
  spacer rows are dropped on short screens instead of pushing content off.
  Check layouts at a big terminal (e.g. 100x36) and small ones (about 34-46
  columns, 20 rows; Connections needs 20 rows for its 16 words).
- Termux has no `/usr/bin/env`, so no `#!/usr/bin/env` shebangs in scripts or
  justfile recipes. Use one-line sh recipes.
- Keep syntax compatible with older Pythons: use `Optional[str]`, not `str | None`.
- Keys: the user navigates with h/j/k/l and arrow keys. Where there's only one axis,
  h/l move left/right. j/k are for vertical movement (or switching kinds/groups),
  not a second left/right. Every game shows its controls on `0`; keep the
  descriptions short and general ("enter: show moves / confirm").

## Layout

- `main.py`: the menu; lists the games as `WordGame(name, scene_fn, color)`.
- `<game>/scene.py`: the game logic class plus a `<game>_scene(stdscr)` loop.
  `<game>/scrape.py` holds the puzzle fetching and a `load_<game>_data(stdscr)`
  that runs it behind `loading_scene.run_loading_animation`.
- `providers.py`: each game's ordered puzzle sources (`providers_for`,
  `get_puzzle`, `ProviderError`). Errors go to `~/.wordgames/providers.log`.
  A started puzzle is locked for its date; an unstarted fallback puzzle is
  replaced when a better provider posts one.
- `nyt.py`: NYT data feeds (not an official API); `_get` is the shared urllib
  GET with a browser user agent.
- `store.py`: `~/.wordgames/<game>/<YYYY-MM-DD>.json` records
  `{game, date, provider, puzzle, progress}`, plus `settings.json`.
  `store.save_progress(record, {...})` saves a game's state.
- `utils.py`:
  - `SafeWindow` makes drawing off-screen harmless.
  - `Palette` gives the colours (colour pair = xterm colour index + 1).
  - Also has the centring helpers.
- `info_panel.py`: the shared full-screen panel: `show` for pages of text and
  `show_controls` for the controls list (wraps long descriptions).
- `placeholder_scene.py`: shown when no provider has a puzzle.

### Game notes

- **Parseword**: from `parseword.com/puzzles/<date>.json`.
  - Only today's and yesterday's puzzles are public; other dates return 403.
    Today's isn't out until some hours after midnight Eastern, so the game falls
    back to yesterday's until then.
  - `parseword/game.py` is a port of the site's move generators (synonyms,
    selection/deletion, reverse, anagram, cycle, container, charade, hidden word).
  - There's no score and no hints. Undo is unlimited, and the puzzle locks once solved.
- **Strands**: any letters can be typed. Letters past the longest part that can
  be placed on the board are shown in gray, as Spelling Bee does with letters
  not in the puzzle.
- **Mini**: a solved puzzle is locked: no edits, so the timer can't restart.

## Testing

There's no test suite beyond the old `test.py` scraper checks. Verify changes by
driving the real app:

- Use a throwaway `HOME` containing
  `.wordgames/<game>/<today>.json` with a hand-made or downloaded puzzle, so
  runs need no network and don't touch the user's saved games.
- Run `python3 main.py` in a pty (`pty.fork`) with `TERM=xterm-256color`,
  `LINES=24` and `COLUMNS=60` (or narrower). Send keystrokes with short delays,
  then render the output with `pyte` and check the text and colours.
  - Menu order: wordle, connections, mini, strands, spellingbee, parseword
    (`j` x N, then Enter).
  - Delete is `\x7f`.
- Install `pyte` in a scratch venv, not in the project.
