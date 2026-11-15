from pathlib import Path
import base64
import lzma


ROOT = Path(__file__).resolve().parent.parent

BITBOARD_FILE = ROOT / "src" / "bitboard.py"
BOOK_READER_FILE = ROOT / "src" / "v7_book.py"
COMPILED_FILE = ROOT / "src" / "v7_compiled.py"

BOOK_FILE = (
    ROOT
    / "data"
    / "v7"
    / "book_d12.bin"
)

OUTPUT_FILE = (
    ROOT
    / "submission.py"
)


def clean_module(text):
    lines = text.splitlines()

    cleaned = []
    skipping_import = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("from src."):
            if (
                "(" in line
                and ")" not in line
            ):
                skipping_import = True

            continue

        if skipping_import:
            if ")" in line:
                skipping_import = False

            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def wrap_encoded(
    encoded,
    width=100,
):
    return "\n".join(
        f'    "{encoded[i:i + width]}"'
        for i in range(
            0,
            len(encoded),
            width,
        )
    )


def main():
    bitboard_code = clean_module(
        BITBOARD_FILE.read_text()
    )

    book_code = clean_module(
        BOOK_READER_FILE.read_text()
    )

    compiled_code = clean_module(
        COMPILED_FILE.read_text()
    )

    raw = BOOK_FILE.read_bytes()

    compressed = lzma.compress(
        raw,
        preset=9,
    )

    encoded = base64.b85encode(
        compressed
    ).decode("ascii")

    encoded_literal = wrap_encoded(
        encoded
    )

    submission = f'''# ============================================================
# ConnectX V7
#
# Self-contained Kaggle agent.
#
# - 9,188,816-position depth-12 exact book
# - Exact strong Connect Four solver
# - Numba-compiled Negamax
# - Alpha-beta / null-window solving
# - Non-losing move pruning
# - Symmetry-aware transposition table
#
# Generated automatically. Do not edit manually.
# ============================================================

import base64
import bisect
import lzma
import struct
import time
from pathlib import Path

import numpy as np
from numba import njit


# ============================================================
# BITBOARD
# ============================================================

{bitboard_code}


# ============================================================
# EMBEDDED DEPTH-12 BOOK
# ============================================================

BOOK_DATA_B85 = (
{encoded_literal}
)

_BOOK_RAW = None


def _load_embedded_book():
    global _BOOK_RAW

    if _BOOK_RAW is None:
        compressed = base64.b85decode(
            BOOK_DATA_B85.encode("ascii")
        )

        _BOOK_RAW = lzma.decompress(
            compressed
        )

    return _BOOK_RAW


# ============================================================
# V7 BOOK READER
# ============================================================

{book_code}


class EmbeddedV7OpeningBook(V7OpeningBook):
    def __init__(self):
        self.path = None

        self.data = (
            _load_embedded_book()
        )

        (
            magic,
            version,
            self.count,
            self.block_count,
        ) = HEADER.unpack_from(
            self.data,
            0,
        )

        if magic != MAGIC:
            raise ValueError(
                "Invalid embedded V7 book"
            )

        if version != VERSION:
            raise ValueError(
                "Unsupported embedded V7 book"
            )

        index_start = HEADER.size

        self.payload_start = (
            index_start
            + self.block_count
            * BLOCK_RECORD.size
        )

        self.block_keys = []
        self.block_offsets = []

        for index in range(
            self.block_count
        ):
            key, offset = (
                BLOCK_RECORD.unpack_from(
                    self.data,
                    index_start
                    + index
                    * BLOCK_RECORD.size,
                )
            )

            self.block_keys.append(
                key
            )

            self.block_offsets.append(
                offset
            )

        self.payload = memoryview(
            self.data
        )[self.payload_start:]


# ============================================================
# COMPILED EXACT SOLVER
# ============================================================

{compiled_code}


# ============================================================
# AGENT
# ============================================================

BOOK = EmbeddedV7OpeningBook()


def exact_parent_score(
    p1,
    p2,
    player,
):
    score = BOOK.lookup(
        p1,
        p2,
        player,
    )

    if score is not None:
        return int(score)

    mask = p1 | p2

    current = (
        p1
        if player == 1
        else p2
    )

    moves_played = (
        mask.bit_count()
    )

    nodes = np.zeros(
        1,
        dtype=np.int64,
    )

    hits = np.zeros(
        1,
        dtype=np.int64,
    )

    age = next_tt_age()

    score = solve(
        np.uint64(current),
        np.uint64(mask),
        moves_played,
        nodes,
        hits,
        TT_KEYS,
        TT_VALUES,
        TT_FLAGS,
        TT_DEPTHS,
        TT_AGES,
        age,
    )

    return int(score)


def choose_move(
    p1,
    p2,
    player,
):
    score = exact_parent_score(
        p1,
        p2,
        player,
    )

    move, _, _ = find_optimal_move(
        p1,
        p2,
        player,
        score,
    )

    if move < 0:
        legal = valid_moves(
            p1,
            p2,
        )

        if not legal:
            return 0

        return int(legal[0])

    return int(move)


def agent(
    observation,
    configuration,
):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    return choose_move(
        p1,
        p2,
        observation.mark,
    )
'''

    OUTPUT_FILE.write_text(
        submission
    )

    print(
        "Generated:",
        OUTPUT_FILE,
    )

    print(
        "Raw V7 book:",
        f"{len(raw) / 1024**2:.2f} MB",
    )

    print(
        "Compressed book:",
        f"{len(compressed) / 1024**2:.2f} MB",
    )

    print(
        "Encoded book:",
        f"{len(encoded) / 1024**2:.2f} MB",
    )

    print(
        "submission.py:",
        f"{OUTPUT_FILE.stat().st_size / 1024**2:.2f} MB",
    )


if __name__ == "__main__":
    main()