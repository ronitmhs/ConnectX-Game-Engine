import struct
from pathlib import Path

from src.bitboard import play_move

from src.compact_book import (
    CompactOpeningBook,
    mirror_bitboard,
    mirror_move,
    mirror_move_mask,
)


BOOK = Path(
    "data/opening_book/book_d8.bin"
)

RECORD = struct.Struct("<QQbB")


def load_book():
    book = {}

    with BOOK.open("rb") as f:
        while True:
            data = f.read(RECORD.size)

            if not data:
                break

            assert len(data) == RECORD.size

            p1, p2, score, move_mask = (
                RECORD.unpack(data)
            )

            book[(p1, p2)] = (
                score,
                move_mask,
            )

    return book


def position_from_sequence(sequence):
    p1 = 0
    p2 = 0
    player = 1

    for char in sequence:
        col = int(char) - 1

        p1, p2 = play_move(
            p1,
            p2,
            col,
            player,
        )

        player = 3 - player

    return p1, p2


def mask_to_moves(mask):
    return [
        col
        for col in range(7)
        if mask & (1 << col)
    ]


def test_book_record_count():
    book = load_book()

    assert len(book) == 129498


def test_empty_board():
    book = load_book()

    score, mask = book[(0, 0)]

    assert score == 1
    assert mask_to_moves(mask) == [3]


def test_sequence_4():
    book = load_book()

    p1, p2 = position_from_sequence("4")

    score, mask = book[(p1, p2)]

    assert score == -1
    assert mask_to_moves(mask) == [3]


def test_sequence_44():
    book = load_book()

    p1, p2 = position_from_sequence("44")

    score, mask = book[(p1, p2)]

    assert score == 1
    assert mask_to_moves(mask) == [3]


def test_sequence_443():
    book = load_book()

    p1, p2 = position_from_sequence("443")

    score, mask = book[(p1, p2)]

    assert score == 2
    assert set(mask_to_moves(mask)) == {1, 4}
    
def test_mirror_move():
    assert mirror_move(0) == 6
    assert mirror_move(1) == 5
    assert mirror_move(2) == 4
    assert mirror_move(3) == 3
    assert mirror_move(4) == 2
    assert mirror_move(5) == 1
    assert mirror_move(6) == 0


def test_double_mirror_bitboard():
    p1, p2 = position_from_sequence(
        "443215"
    )

    assert (
        mirror_bitboard(
            mirror_bitboard(p1)
        )
        == p1
    )

    assert (
        mirror_bitboard(
            mirror_bitboard(p2)
        )
        == p2
    )


def test_double_mirror_mask():
    mask = (
        (1 << 0)
        | (1 << 2)
        | (1 << 5)
    )

    assert (
        mirror_move_mask(
            mirror_move_mask(mask)
        )
        == mask
    )