import json
from pathlib import Path


INVALID_SCORE = -1000

DEFAULT_BOOK = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "opening_book"
    / "book_d6.json"
)


class OpeningBook:
    def __init__(self, path=DEFAULT_BOOK):
        self.path = Path(path)

        with self.path.open() as f:
            self.book = json.load(f)

    @staticmethod
    def make_key(p1, p2, player):
        return f"{p1}:{p2}:{player}"

    def get_scores(self, p1, p2, player):
        key = self.make_key(
            p1,
            p2,
            player,
        )

        return self.book.get(key)

    def get_best_moves(self, p1, p2, player):
        scores = self.get_scores(
            p1,
            p2,
            player,
        )

        if scores is None:
            return None

        legal = [
            (score, col)
            for col, score in enumerate(scores)
            if score != INVALID_SCORE
        ]

        if not legal:
            return None

        best_score = max(
            score
            for score, _ in legal
        )

        best_moves = [
            col
            for score, col in legal
            if score == best_score
        ]

        return best_moves

    def choose_move(self, p1, p2, player):
        """
        Deterministic policy for now.

        Among equally solved moves, prefer:
        center, then near-center.
        """

        best_moves = self.get_best_moves(
            p1,
            p2,
            player,
        )

        if not best_moves:
            return None

        order = (
            3, 2, 4, 1, 5, 0, 6
        )

        for col in order:
            if col in best_moves:
                return col

        return best_moves[0]

    def __len__(self):
        return len(self.book)