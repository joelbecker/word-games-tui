# List the recipes
default:
    @just --list

# Play the games
play:
    python main.py

# Delete saved puzzles and progress (all games, or one: just reset wordle). Settings are kept.
reset game="":
    @if [ -n "{{game}}" ]; then rm -rf "$HOME/.wordgames/{{game}}" && echo "Reset {{game}}"; else find "$HOME/.wordgames" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null; echo "Reset all games"; fi
