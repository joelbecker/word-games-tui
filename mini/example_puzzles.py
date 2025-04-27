import random

def parse_puzzle(s: str) -> list[list[str]]:
    return [[c if c.isalpha() else None for c in list(row)] for row in s.strip().split("\n")]


puzzle_1 = """
.ROSE
COUPS
OWNUP
DECRY
EDEN.
"""

puzzle_2 = """
...SIPS
..HELLA
.POLLEN
GOLFBAG
ALLIES.
SKEET..
PARS...
"""

puzzle_3 = """
..PTA
ISAAC
TORCH
TRITE
YES..
"""

puzzle_4 = """
PCS..
ALPS.
NERDS
.FISH
..GUY
"""

puzzle_5 = """
..MAS..
.SILKS.
HELLYES
ELK.DIE
REDWINE
.SUAVE.
..DYE..
"""

examples = [
    puzzle_1,
    puzzle_2,
    puzzle_3,
    puzzle_4,
    puzzle_5
]

random.shuffle(examples)
