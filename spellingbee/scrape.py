import random

import providers
from loading_scene import run_loading_animation


def make_puzzle(center_letter, answers):
    """Build and validate the stored puzzle data."""
    letters = set(center_letter)
    for word in answers:
        if center_letter not in word:
            raise ValueError("solution contains word without center letter: {}".format(word))
        letters.update(word)
    if len(letters) != 7:
        raise ValueError("solution contains wrong number of letters: {}".format(letters))
    return {
        "center_letter": center_letter,
        "letters": "".join(sorted(letters)),
        "answers": list(answers),
    }


class RandomSpellingBeeProvider(providers.Provider):
    """One generated puzzle per day, seeded by the date.

    Picks a 7-letter pangram from the dictionary the game already uses for
    guess checking. Like the NYT puzzle, it never uses the letter S.
    """
    name = "random"
    min_answers = 20
    max_answers = 60

    def fetch(self, game, date):
        import english_dictionary.scripts.read_pickle as dictionary
        words = sorted(
            w for w in dictionary.get_dict()
            if len(w) >= 4 and w.isascii() and w.isalpha() and w.islower() and "s" not in w
        )
        masks = [sum(1 << (ord(c) - 97) for c in set(w)) for w in words]
        pangram_letters = sorted({"".join(sorted(set(w))) for w in words if len(set(w)) == 7})

        rng = random.Random(f"spellingbee:{date}")
        rng.shuffle(pangram_letters)
        for letters in pangram_letters[:500]:
            letters_mask = sum(1 << (ord(c) - 97) for c in letters)
            candidates = [w for w, m in zip(words, masks) if m & ~letters_mask == 0]
            for center_letter in rng.sample(letters, len(letters)):
                answers = [w for w in candidates if center_letter in w]
                if self.min_answers <= len(answers) <= self.max_answers:
                    return make_puzzle(center_letter, answers)
        raise providers.ProviderError("No suitable puzzle found")


def load_spellingbee_data(stdscr):
    stdscr.clear()
    return run_loading_animation(stdscr, lambda: providers.get_puzzle("spellingbee"), "Fetching SpellingBee words...", min_time=0.5)
