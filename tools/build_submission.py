from pathlib import Path
import base64
import lzma
import re


ROOT = Path(__file__).resolve().parent.parent

BITBOARD_FILE = ROOT / "src" / "bitboard.py"
SEARCH_FILE = ROOT / "src" / "search.py"
BOOK_FILE = ROOT / "data" / "opening_book" / "book_d10.bin"

OUTPUT_FILE = ROOT / "submission.py"


def clean_module(text):
    """
    Remove imports that reference our local src package.
    Standard-library imports remain.
    """

    lines = text.splitlines()

    cleaned = []
    skipping_import = False

    for line in lines:
        stripped = line.strip()

        # Handle multiline:
        #
        # from src.bitboard import (
        #     ...
        # )
        if stripped.startswith("from src."):
            if "(" in line and ")" not in line:
                skipping_import = True
            continue

        if skipping_import:
            if ")" in line:
                skipping_import = False
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def encode_book():
    raw = BOOK_FILE.read_bytes()

    compressed = lzma.compress(
        raw,
        preset=9,
    )

    encoded = base64.b85encode(
        compressed
    ).decode("ascii")

    return raw, compressed, encoded


def wrap_encoded_book(encoded, width=100):
    return "\n".join(
        f'    "{encoded[i:i + width]}"'
        for i in range(0, len(encoded), width)
    )


def main():
    bitboard_code = clean_module(
        BITBOARD_FILE.read_text()
    )

    search_code = clean_module(
        SEARCH_FILE.read_text()
    )

    raw, compressed, encoded = encode_book()

    encoded_literal = wrap_encoded_book(
        encoded
    )

    submission = f'''# ============================================================
# ConnectX V6
#
# Self-contained Kaggle competition agent.
#
# Features:
# - Bitboard representation
# - Bitwise win/threat detection
# - Gravity-aware non-losing move pruning
# - Iterative-deepening negamax
# - Alpha-beta pruning
# - Transposition table
# - Solved depth-10 opening book
# - Horizontal symmetry-aware book lookup
# ============================================================

import base64
import lzma
import struct
import time


# ============================================================
# BITBOARD
# ============================================================

{bitboard_code}


# ============================================================
# SEARCH ENGINE
# ============================================================

{search_code}


# ============================================================
# EMBEDDED SOLVED OPENING BOOK
# ============================================================

BOOK_RECORD = struct.Struct("<QQbB")

BOOK_DATA_B85 = (
{encoded_literal}
)

_BOOK = None


def mirror_bitboard(position):
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


def load_opening_book():
    global _BOOK

    if _BOOK is not None:
        return _BOOK

    compressed = base64.b85decode(
        BOOK_DATA_B85.encode("ascii")
    )

    raw = lzma.decompress(
        compressed
    )

    book = {{}}

    size = BOOK_RECORD.size

    if len(raw) % size != 0:
        raise ValueError(
            "Corrupt embedded opening book"
        )

    for offset in range(
        0,
        len(raw),
        size,
    ):
        p1, p2, score, move_mask = (
            BOOK_RECORD.unpack_from(
                raw,
                offset,
            )
        )

        book[(p1, p2)] = (
            score,
            move_mask,
        )

    _BOOK = book

    return _BOOK


def book_lookup(p1, p2):
    book = load_opening_book()

    result = book.get(
        (p1, p2)
    )

    if result is not None:
        return result

    mp1 = mirror_bitboard(p1)
    mp2 = mirror_bitboard(p2)

    result = book.get(
        (mp1, mp2)
    )

    if result is None:
        return None

    score, move_mask = result

    return (
        score,
        mirror_move_mask(move_mask),
    )


def book_best_moves(p1, p2):
    result = book_lookup(
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


def book_choose_move(p1, p2):
    result = book_lookup(
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


# ============================================================
# KAGGLE AGENT
# ============================================================

def agent(observation, configuration):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    # Solved opening theory first.
    book_move = book_choose_move(
        p1,
        p2,
    )

    if book_move is not None:
        return int(book_move)

    # Search after leaving the book.
    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return int(move)
'''

    OUTPUT_FILE.write_text(
        submission
    )

    print("Generated:", OUTPUT_FILE)
    print(
        "Raw book:",
        round(
            len(raw) / 1024 / 1024,
            2,
        ),
        "MB",
    )
    print(
        "Compressed book:",
        round(
            len(compressed) / 1024 / 1024,
            2,
        ),
        "MB",
    )
    print(
        "Encoded book:",
        round(
            len(encoded) / 1024 / 1024,
            2,
        ),
        "MB",
    )
    print(
        "submission.py:",
        round(
            OUTPUT_FILE.stat().st_size
            / 1024
            / 1024,
            2,
        ),
        "MB",
    )


if __name__ == "__main__":
    main()