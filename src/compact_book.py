import struct
from pathlib import Path


RECORD = struct.Struct("<QQbB")

DEFAULT_BOOK = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "opening_book"
    / "book_d10.bin"
)

CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)


def mirror_bitboard(position):
    """
    Horizontally mirror our 7-column bitboard.

    Each column occupies 7 bits:
    6 playable cells + 1 sentinel slot.
    """
    mirrored = 0

    column_mask = (1 << 7) - 1

    for col in range(7):
        column = (
            position >> (col * 7)
        ) & column_mask

        mirrored |= (
            column << ((6 - col) * 7)
        )

    return mirrored


def mirror_move(col):
    return 6 - col


def mirror_move_mask(mask):
    mirrored = 0

    for col in range(7):
        if mask & (1 << col):
            mirrored |= (
                1 << mirror_move(col)
            )

    return mirrored


class CompactOpeningBook:
    def __init__(self, path=DEFAULT_BOOK):
        self.path = Path(path)
        self.book = {}

        self._load()

    def _load(self):
        with self.path.open("rb") as f:
            while True:
                data = f.read(RECORD.size)

                if not data:
                    break

                if len(data) != RECORD.size:
                    raise ValueError(
                        "Corrupt opening-book record"
                    )

                p1, p2, score, move_mask = (
                    RECORD.unpack(data)
                )

                self.book[(p1, p2)] = (
                    score,
                    move_mask,
                )

    def lookup(self, p1, p2):
        """
        Lookup exact position first.

        If absent, try the horizontally mirrored
        equivalent position and mirror its moves back.
        """

        result = self.book.get(
            (p1, p2)
        )

        if result is not None:
            return result

        mp1 = mirror_bitboard(p1)
        mp2 = mirror_bitboard(p2)

        mirrored_result = self.book.get(
            (mp1, mp2)
        )

        if mirrored_result is None:
            return None

        score, move_mask = mirrored_result

        return (
            score,
            mirror_move_mask(move_mask),
        )

    def get_best_moves(self, p1, p2):
        result = self.lookup(
            p1,
            p2,
        )

        if result is None:
            return None

        _, move_mask = result

        return [
            col
            for col in range(7)
            if move_mask & (1 << col)
        ]

    def choose_move(self, p1, p2):
        result = self.lookup(
            p1,
            p2,
        )

        if result is None:
            return None

        _, move_mask = result

        for col in CENTER_ORDER:
            if move_mask & (1 << col):
                return col

        return None

    def score(self, p1, p2):
        result = self.lookup(
            p1,
            p2,
        )

        if result is None:
            return None

        return result[0]

    def __len__(self):
        return len(self.book)