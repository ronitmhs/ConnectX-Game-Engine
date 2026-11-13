from pathlib import Path
import base64
import lzma


ROOT = Path(__file__).resolve().parent.parent

BITBOARD_FILE = ROOT / "src" / "bitboard.py"
SEARCH_FILE = ROOT / "src" / "search.py"
BOOK_FILE = (
    ROOT
    / "data"
    / "opening_book"
    / "book_d10.bin"
)

OUTPUT_FILE = ROOT / "submission.py"


def clean_module(text):
    """
    Remove imports that reference our local src package.

    Standard-library imports remain because submission.py
    can use Python's built-in modules.
    """

    lines = text.splitlines()

    cleaned = []
    skipping_import = False

    for line in lines:
        stripped = line.strip()

        # Remove local imports such as:
        #
        # from src.bitboard import (
        #     ...
        # )
        #
        # or:
        #
        # from src.bitboard import something

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


def encode_book():
    """
    Compress the depth-10 binary opening book with LZMA
    and encode it as Base85 so it can live inside one
    Python submission file.
    """

    raw = BOOK_FILE.read_bytes()

    compressed = lzma.compress(
        raw,
        preset=9,
    )

    encoded = base64.b85encode(
        compressed
    ).decode("ascii")

    return (
        raw,
        compressed,
        encoded,
    )


def wrap_encoded_book(
    encoded,
    width=100,
):
    """
    Split the Base85 string into manageable Python
    string literals.
    """

    return "\n".join(
        f'    "{encoded[i:i + width]}"'
        for i in range(
            0,
            len(encoded),
            width,
        )
    )


def main():
    # ========================================================
    # READ CURRENT ENGINE
    # ========================================================

    bitboard_code = clean_module(
        BITBOARD_FILE.read_text()
    )

    search_code = clean_module(
        SEARCH_FILE.read_text()
    )

    # ========================================================
    # EMBED OPENING BOOK
    # ========================================================

    raw, compressed, encoded = (
        encode_book()
    )

    encoded_literal = (
        wrap_encoded_book(
            encoded
        )
    )

    # ========================================================
    # BUILD SELF-CONTAINED SUBMISSION
    # ========================================================

    submission = f'''# ============================================================
# ConnectX V6B
#
# Self-contained Kaggle competition agent.
#
# Architecture:
#
# EARLY GAME
# - Solved depth-10 opening book
# - 1,208,493 solved positions
# - Horizontal symmetry-aware lookup
#
# MIDDLEGAME
# - Bitboard negamax
# - Alpha-beta pruning
# - Iterative deepening
# - Transposition table
# - Gravity-aware threat detection
# - Non-losing move pruning
#
# ENDGAME
# - Direct exact-to-terminal search
# - Activates with <= 23 empty cells
#
# No external files or local src imports required.
# ============================================================

import base64
import lzma
import struct
import time


# ============================================================
# BITBOARD ENGINE
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
    """
    Horizontally mirror the 7-column bitboard.

    Each Connect Four column occupies seven bits:
    six playable cells plus one sentinel bit.
    """

    mirrored = 0

    column_mask = (
        (1 << 7) - 1
    )

    for col in range(7):
        column = (
            position
            >> (col * 7)
        ) & column_mask

        mirrored |= (
            column
            << ((6 - col) * 7)
        )

    return mirrored


def mirror_move(col):
    return 6 - col


def mirror_move_mask(mask):
    mirrored = 0

    for col in range(7):
        if mask & (1 << col):
            mirrored |= (
                1
                << mirror_move(col)
            )

    return mirrored


def load_opening_book():
    """
    Decode and decompress the embedded opening book once.

    The resulting dictionary is cached globally for all
    later agent calls.
    """

    global _BOOK

    if _BOOK is not None:
        return _BOOK

    compressed = base64.b85decode(
        BOOK_DATA_B85.encode(
            "ascii"
        )
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
        (
            p1,
            p2,
            score,
            move_mask,
        ) = BOOK_RECORD.unpack_from(
            raw,
            offset,
        )

        book[(p1, p2)] = (
            score,
            move_mask,
        )

    _BOOK = book

    return _BOOK


def book_lookup(p1, p2):
    """
    Exact lookup first.

    If the exact orientation is absent, try the
    horizontally mirrored position.
    """

    book = load_opening_book()

    result = book.get(
        (p1, p2)
    )

    if result is not None:
        return result

    mp1 = mirror_bitboard(
        p1
    )

    mp2 = mirror_bitboard(
        p2
    )

    result = book.get(
        (mp1, mp2)
    )

    if result is None:
        return None

    score, move_mask = result

    return (
        score,
        mirror_move_mask(
            move_mask
        ),
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
        if move_mask
        & (1 << col)
    ]


def book_choose_move(p1, p2):
    """
    Choose a solved optimal opening move.

    Prefer center-oriented moves when several moves
    have the same solved score.
    """

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
# V6B SEARCH SETTINGS
# ============================================================

SEARCH_TIME = 1.65

# Exact endgame gets its own smaller budget.
# If exact search times out, choose_move_exact()
# returns a safe fallback rather than launching
# another full search.
EXACT_TIME = 1.40

# At 23 or fewer empty cells, attempt a direct
# terminal-depth solve.
EXACT_ENDGAME_EMPTIES = 23


# ============================================================
# KAGGLE AGENT
# ============================================================

def agent(
    observation,
    configuration,
):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    # --------------------------------------------------------
    # 1. SOLVED OPENING BOOK
    # --------------------------------------------------------

    book_move = book_choose_move(
        p1,
        p2,
    )

    if book_move is not None:
        return int(
            book_move
        )

    # --------------------------------------------------------
    # 2. EXACT ENDGAME
    # --------------------------------------------------------

    ply = (
        p1 | p2
    ).bit_count()

    empties = 42 - ply

    if (
        empties
        <= EXACT_ENDGAME_EMPTIES
    ):
        engine = SearchEngine(
            time_limit=EXACT_TIME
        )

        move = (
            engine.choose_move_exact(
                p1,
                p2,
                player,
                depth=empties,
            )
        )

        # choose_move_exact() returns a safe fallback
        # if the terminal search exceeds its budget.
        #
        # None should therefore occur only when there
        # is no legal move.
        if move is not None:
            return int(
                move
            )

    # --------------------------------------------------------
    # 3. TIMED MIDDLEGAME SEARCH
    # --------------------------------------------------------

    engine = SearchEngine(
        time_limit=SEARCH_TIME
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return int(
        move
    )
'''

    # ========================================================
    # WRITE OUTPUT
    # ========================================================

    OUTPUT_FILE.write_text(
        submission
    )

    # ========================================================
    # BUILD REPORT
    # ========================================================

    print(
        "Generated:",
        OUTPUT_FILE,
    )

    print(
        "Raw book:",
        round(
            len(raw)
            / 1024
            / 1024,
            2,
        ),
        "MB",
    )

    print(
        "Compressed book:",
        round(
            len(compressed)
            / 1024
            / 1024,
            2,
        ),
        "MB",
    )

    print(
        "Encoded book:",
        round(
            len(encoded)
            / 1024
            / 1024,
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

    print()
    print(
        "V6B exact cutoff:",
        23,
        "empty cells",
    )

    print(
        "Exact-search budget:",
        1.40,
        "seconds",
    )

    print(
        "Middlegame budget:",
        1.65,
        "seconds",
    )


if __name__ == "__main__":
    main()