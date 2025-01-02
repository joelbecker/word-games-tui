from dataclasses import dataclass


def score_word(word: str) -> int:
    if len(word) < 4:
        return 0
    if len(word) == 4:
        return 1
    else:
        return len(word)


def get_rank(score: int, max_score: int) -> str:
    percentage = score / max_score
    if percentage < 0.02:
        return "Beginner"
    elif percentage < 0.05:
        return "Good Start"
    elif percentage < 0.08:
        return "Moving Up"
    elif percentage < 0.15:
        return "Good"
    elif percentage < 0.25:
        return "Solid"
    elif percentage < 0.40:
        return "Nice"
    elif percentage < 0.50:
        return "Great"
    elif percentage < 0.70:
        return "Amazing"
    elif percentage < 1:
        return "Genius"
    else:
        return "Queen Bee"


@dataclass
class GuessResult:
    word: str
    score: int
    is_valid: bool
    is_correct: bool
    message: str


class SpellingBeeGame:
    def __init__(self, letters, center_letter, solution_words, dictionary, score: int = 0):
        self.letters = set(letters)
        self.center_letter = center_letter
        self.solution_words = set(solution_words)
        self.dictionary = set(dictionary)
        self.score = score
        self.max_score = sum(score_word(word) for word in self.solution_words)
        self.message = "Welcome to Spelling Bee demo!"

    def evaluate_guess(self, word: str) -> GuessResult:
        if word in self.solution_words:
            return GuessResult(word, score_word(word), True, True, f"{word} is correct!")
        if word in self.dictionary:
            return GuessResult(word, 0, True, False, f"{word} is valid but not the solution")
        if len(word) < 4:
            return GuessResult(word, 0, False, False, "Too short")
        if word not in self.dictionary:
            return GuessResult(word, 0, False, False, "Not a word")
        if self.center_letter not in word:
            return GuessResult(word, 0, False, False, "Must contain the center letter")
        if set(word) - self.letters:
            return GuessResult(word, 0, False, False, "Bad letters")
        if word not in self.solution_words:
            return GuessResult(word, 0, True, False, "Word not in dictionary")
        return GuessResult(word, 0, False, False, "An error occurred")

    def guess(self, word: str) -> GuessResult:
        result = self.evaluate_guess(word)
        if result.is_correct:
            self.score += result.score
        self.message = result.message
        return result
