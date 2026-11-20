"""Parseword rules, independent of the display.

The phrase is a list of tokens. The player selects adjacent tokens and
replaces them with one of the moves on offer:

* synonyms (the puzzle's "synonyms", decoys included) and its jokes
  ("extraReplacements")
* wordplay worked out from indicator words in the selection, using the
  puzzle's "wordTypes". The generators follow parseword.com's: an indicator
  acts on the "fodder" words before and/or after it in the selection.
* joining several words into one
* the puzzle's own solving step, when the selection is exactly its "before".
  This keeps every puzzle solvable, since the site also knows indicators
  that the puzzle file doesn't list.
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

TYPE_LABELS = {
    "substitution": "Synonym",
    "charade": "Join",
    "hidden_word": "Hidden word",
}

# Selection/deletion subtypes (parseword.com's numbering)
HEAD, TAIL, INNER, OUTER, ALTERNATING, PHRASE, INDEX, LETTERS, EVERY_LETTER, \
    FODDER_FIRST_REMOVAL, DELETION_FIRST_REMOVAL, OUTER_PHRASE = range(1, 13)
VOWELS = set("aeiou")
MAX_OPTIONS = {"anagram": 3, "container": 1, "hidden_word": 3}  # Per indicator, as on the site
HIDDEN_WORD_MAX = 16


def normalize(text: str) -> str:
    """Lowercase letters only, for matching words against the puzzle data."""
    return re.sub(r"[^a-z]", "", text.lower())


def clean_phrase(text: str) -> str:
    """Joke phrases look like '*👾 Scientology?*': drop the markup and emoji,
    which a phone terminal may not be able to draw."""
    text = "".join(c for c in text.strip("*") if ord(c) < 0x2000 and unicodedata.category(c)[0] != "S")
    return " ".join(text.split())


def type_label(kind: str) -> str:
    return TYPE_LABELS.get(kind, kind.replace("_", " ").capitalize())


@dataclass
class Token:
    text: str                 # As displayed
    key: str                  # normalize(text)
    transformed: bool = False
    definition: bool = False


@dataclass
class Option:
    kind: str
    indicator: Optional[str]   # The indicator words, as in the phrase
    result: str
    indicator_positions: tuple = ()  # Token indices within the selection

    @property
    def heading(self) -> str:
        return f"{type_label(self.kind)} ({self.indicator})" if self.indicator else type_label(self.kind)


# Generators: (word type, fodder words before, fodder words after) -> results

def _one_side(before, after):
    if before and after:
        return None  # These types need contiguous fodder on one side
    return before or after


def _shorten(kind, joined, words, sub, count_type, n):
    """Head/tail/inner/outer selections and deletions."""
    keep = kind == "selection"
    pct = count_type == 1
    from_end = False
    if sub in (TAIL, INNER):
        if pct:
            n = 1 - n
        else:
            from_end = True
        sub = HEAD if sub == TAIL else OUTER
        keep = not keep
    elif not sub:
        sub = HEAD

    def amount(length):
        return round(length * n) if pct else (length - n if from_end else n)

    if sub == HEAD:
        out = ""
        for w in words:
            g = max(1, min(len(w) - 1, amount(len(w))))
            out += w[:g] if keep else w[g:]
    elif sub == OUTER:
        out = ""
        for w in words:
            g = max(1, min(len(w) - 1, 0.5 * (int(len(w) * n) if pct else amount(len(w)))))
            if keep and 2 * g >= len(w):
                return ""
            g = int(g)
            out += w[:g] + w[len(w) - g:] if keep else w[g:len(w) - g]
    elif sub == OUTER_PHRASE:
        g = max(1, min(len(joined) - 1, 0.5 * (int(len(joined) * n) if pct else amount(len(joined)))))
        if keep and 2 * g >= len(joined):
            return ""
        g = int(g)
        out = joined[:g] + joined[len(joined) - g:] if keep else joined[g:len(joined) - g]
    else:
        return ""
    return out if out != joined else ""


def _pick(kind, joined, indices):
    if kind == "selection":
        return "".join(c for i, c in enumerate(joined) if i in indices)
    return "".join(c for i, c in enumerate(joined) if i not in indices)


def _removals(fodder, removed, remove_all):
    fodder, removed = "".join(fodder), "".join(removed)
    if not removed or removed not in fodder:
        return []
    if remove_all:
        return [fodder.replace(removed, "")]
    return list(dict.fromkeys(fodder[:m.start()] + fodder[m.end():] for m in re.finditer(re.escape(removed), fodder)))


def gen_selection(t, before, after):
    kind, sub = t["type"], t.get("subType") or HEAD
    if sub == FODDER_FIRST_REMOVAL:
        return _removals(before, after, t.get("removeAll"))
    if sub == DELETION_FIRST_REMOVAL:
        return _removals(after, before, t.get("removeAll"))
    words = _one_side(before, after)
    if not words:
        return []
    joined = "".join(words)
    if sub == ALTERNATING:
        if len(joined) < 2:
            return []
        return [_pick(kind, joined, set(range(t.get("offset", 0), len(joined), t.get("step", 2))))]
    if sub == PHRASE:
        phrase = t.get("phrase") or ""
        start = joined.find(phrase) if phrase else -1
        return [_pick(kind, joined, set(range(start, start + len(phrase))))] if start >= 0 else []
    if sub == LETTERS:
        letters = set(t.get("phrase") or "")
        if not letters or not letters <= set(joined):
            return []
        return [_pick(kind, joined, {i for i, c in enumerate(joined) if c in letters})]
    if sub == INDEX:
        return [_pick(kind, joined, set(t["indices"]))] if t.get("indices") else []
    if sub == EVERY_LETTER:
        if kind == "selection":
            return list(joined)
        return [joined[:i] + joined[i + 1:] for i in range(len(joined))]
    if sub in (HEAD, TAIL, INNER, OUTER, OUTER_PHRASE):
        return [_shorten(kind, joined, words, sub, t.get("countType", 0), t.get("count", 1))]
    return []


def gen_reverse(t, before, after):
    words = _one_side(before, after)
    return ["".join(words)[::-1]] if words else []


def scrambles(letters: str):
    """Deterministic decoy anagrams (the site's fallback shuffle)."""
    seen = []
    for e in range(10):
        chars = list(letters)
        for r in range(len(chars) - 1, 0, -1):
            n = (ord(letters[r]) + e * 7) % (r + 1)
            chars[r], chars[n] = chars[n], chars[r]
        word = "".join(chars)
        if word != letters and word not in seen:
            seen.append(word)
    return seen


def gen_anagram(t, before, after):
    words = _one_side(before, after)
    letters = "".join(words or [])
    return scrambles(letters) if len(letters) >= 3 else []


def _rotate(word, n, backward=False):
    if backward:
        n = len(word) - n
    return word[n:] + word[:n]


def gen_cycle(t, before, after):
    words = _one_side(before, after)
    word = "".join(words or [])
    if len(word) < 2:
        return []
    sub = t.get("subType") or 3
    if sub in (1, 2):
        count = t.get("count", 1)
        n = round(len(word) * count) if t.get("countType") == 1 else count
        n = max(1, min(len(word) - 1, n))
        rotated = _rotate(word, n, backward=sub == 2)
        return [rotated] if rotated != word else []
    return list(dict.fromkeys(r for r in (_rotate(word, n) for n in range(1, len(word))) if r != word))


def _insert(inner, outer):
    """Put inner inside outer at a plausible spot (the site's heuristic)."""
    if len(outer) < 2:
        return ""
    consonant = inner[0] not in VOWELS
    spots = [n for n in range(len(outer) - 2) if (outer[n] in VOWELS) == consonant]
    at = 1 + spots[-(-len(spots) // 2) - 1] if spots else len(outer) // 2
    return outer[:at] + inner + outer[at:]


def gen_container(t, before, after):
    position, sub = t.get("indicatorPosition", 0), t.get("subType", 0)
    results = []
    if position == 0:  # Standard: fodder on both sides
        if not before or not after:
            return []
        if sub in (0, 1):
            results.append(_insert("".join(before), "".join(after)))
        if sub in (0, 2):
            results.append(_insert("".join(after), "".join(before)))
    else:  # Prefix (1) or postfix (2): all the fodder on one side
        fodder = after if position == 1 else before
        if (before if position == 1 else after) or len(fodder) < 2:
            return []
        if sub in (0, 1):
            results.append(_insert(fodder[-1], "".join(fodder[:-1])))
        if sub in (0, 2):
            results.append(_insert(fodder[0], "".join(fodder[1:])))
    return [r for r in results if r]


def gen_charade(t, before, after):
    if not before or not after:
        return []
    sub = t.get("subType") or 2
    if sub == 2:
        return ["".join(before + after)]
    if sub == 3:
        return ["".join(after + before)]
    return []


def gen_hidden_word(t, before, after):
    words = _one_side(before, after)
    if not words:
        return []
    if len(words) == 1:
        return [words[0][1:-1]] if len(words[0]) >= 3 else []
    inner = "".join(words[1:-1])
    room = HIDDEN_WORD_MAX - len(inner)
    if room < 2:
        return []
    first, last = words[0], words[-1]
    a = min(len(first) - 1, room // 2)
    b = min(len(last) - 1, room - a)
    if not a or not b:
        return []
    h = len(inner) % a + 1
    c = (len(first) + len(last)) % b + 1
    return [first[-h:] + inner + last[:c]]


GENERATORS = {
    "selection": gen_selection, "deletion": gen_selection, "reverse": gen_reverse,
    "anagram": gen_anagram, "cycle": gen_cycle, "container": gen_container,
    "charade": gen_charade, "hidden_word": gen_hidden_word,
}


class ParsewordGame:
    def __init__(self, puzzle: dict, steps: list = ()):
        self.puzzle = puzzle
        self.solution = normalize(puzzle["solution"])
        self.synonyms = {self._key(k): v for k, v in (puzzle.get("synonyms") or {}).items()}
        self.extras = {self._key(k): v for k, v in (puzzle.get("extraReplacements") or {}).items()}
        self.word_types = {self._key(k): v for k, v in (puzzle.get("wordTypes") or {}).items()}
        self.mutations = puzzle["mutations"]
        self.linking = self._key(puzzle.get("linking") or "")
        self.steps = []
        self.tokens = self._initial_tokens()
        for step in steps:
            self.apply(step)

    @staticmethod
    def _key(phrase: str) -> str:
        return " ".join(normalize(w) for w in phrase.split() if normalize(w))

    def _initial_tokens(self):
        tokens = [Token(w, normalize(w)) for w in self.puzzle["puzzle"].split() if normalize(w)]
        definition = self._key(self.puzzle["definition"]).split()
        keys = [t.key for t in tokens]
        # The definition is at one end of the phrase; prefer the start
        n = len(definition)
        if keys[:n] == definition:
            span = range(n)
        elif keys[-n:] == definition:
            span = range(len(keys) - n, len(keys))
        else:
            span = next((range(i, i + n) for i in range(len(keys)) if keys[i:i + n] == definition), range(0))
        for i in span:
            tokens[i].definition = True
        return tokens

    # State

    @property
    def is_solved(self) -> bool:
        rest = [t for t in self.tokens if not t.definition]
        if self.linking:
            # A linking word ("in", "for", ...) between the definition and the
            # wordplay is allowed to stay
            links = self.linking.split()
            n = len(links)
            if [t.key for t in rest[:n]] == links and not any(t.transformed for t in rest[:n]):
                rest = rest[n:]
            elif [t.key for t in rest[-n:]] == links and not any(t.transformed for t in rest[-n:]):
                rest = rest[:-n]
        return len(rest) == 1 and rest[0].key == self.solution

    def selectable(self, i: int) -> bool:
        return 0 <= i < len(self.tokens) and not self.tokens[i].definition

    # Moves

    def options(self, start: int, end: int) -> list:
        """Moves for tokens[start:end], grouped by heading in a stable order."""
        selection = self.tokens[start:end]
        if not selection or any(t.definition for t in selection):
            return []
        keys = [t.key for t in selection]
        phrase = " ".join(keys)
        found = []

        for word in self.synonyms.get(phrase, []):
            found.append(Option("substitution", None, word))
        for extra in self.extras.get(phrase, []):
            if isinstance(extra, str):
                found.append(Option("substitution", None, clean_phrase(extra)))
            else:
                found.append(Option(extra.get("type", "substitution"), extra.get("indicator"), clean_phrase(extra["phrase"])))

        for i in range(len(keys)):
            for j in range(i + 1, len(keys) + 1):
                indicator = " ".join(keys[i:j])
                for t in self.word_types.get(indicator, []):
                    found += self._generate(t, keys, i, j, selection)

        if len(keys) > 1:
            found.append(Option("charade", None, "".join(keys)))

        for m in self.mutations:
            if self._key(m["before"]) == phrase:
                positions = self._positions(keys, m.get("indicator"))
                found.append(Option(m["type"], self._display(selection, positions) if positions else m.get("indicator"),
                                    m["after"], positions))

        return self._group(found)

    def _generate(self, t, keys, i, j, selection):
        before, after = keys[:i], keys[j:]
        if t.get("fodderBefore") is False and before or t.get("fodderAfter") is False and after:
            return []
        fodder = len(before) + len(after)
        if not fodder or t.get("maxFodderWords") and fodder > t["maxFodderWords"] \
                or t.get("minFodderWords") and fodder < t["minFodderWords"]:
            return []
        generator = GENERATORS.get(t.get("type"))
        if not generator:
            return []
        results = [r for r in generator(t, before, after) if r]
        results = results[:MAX_OPTIONS.get(t["type"], 10)]
        positions = tuple(range(i, j))
        return [Option(t["type"], self._display(selection, positions), r, positions) for r in results]

    @staticmethod
    def _positions(keys, indicator):
        if not indicator:
            return ()
        words = [normalize(w) for w in indicator.split() if normalize(w)]
        for i in range(len(keys) - len(words) + 1):
            if keys[i:i + len(words)] == words:
                return tuple(range(i, i + len(words)))
        return ()

    @staticmethod
    def _display(selection, positions):
        return " ".join(selection[p].key for p in positions)

    @staticmethod
    def _group(found):
        """[(heading, indicator positions, [Option, ...]), ...] without duplicates."""
        groups = {}
        for option in found:
            option.result = option.result.lower() if option.kind != "substitution" or option.result.isalpha() else option.result
            group = groups.setdefault(option.heading, (option.heading, option.indicator_positions, []))
            if all(o.result != option.result for o in group[2]):
                group[2].append(option)
        for heading, _, opts in groups.values():
            if opts[0].kind == "anagram":
                opts.sort(key=lambda o: o.result)  # Don't give the answer away by position
        return list(groups.values())

    def apply(self, step: dict):
        """step: {"start", "end", "result", "type", "indicator"}"""
        start, end = step["start"], step["end"]
        before = self.tokens[start:end]
        step = dict(step, before=" ".join(t.key for t in before))
        self.tokens[start:end] = [Token(step["result"], normalize(step["result"]), transformed=True)]
        self.steps.append(step)

    def undo(self):
        """Undo the last step; returns it, or None at the start."""
        if not self.steps:
            return None
        last = self.steps[-1]
        steps = [{k: s[k] for k in ("start", "end", "result", "type", "indicator")} for s in self.steps[:-1]]
        self.steps = []
        self.tokens = self._initial_tokens()
        for step in steps:
            self.apply(step)
        return last
