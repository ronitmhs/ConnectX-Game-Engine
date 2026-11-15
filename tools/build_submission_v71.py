from pathlib import Path
import base64
import lzma
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent

V6_BUILDER = (
    ROOT
    / "tools"
    / "build_submission.py"
)

V7_BOOK_READER_FILE = (
    ROOT
    / "src"
    / "v7_book.py"
)

V7_BOOK_FILE = (
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
    """
    Remove imports of local src modules.

    Standard-library imports remain.
    """

    lines = text.splitlines()

    cleaned = []
    skipping_import = False
    skipping_default_book = False

    for line in lines:
        stripped = line.strip()
        
        # Remove v7_book.py's filesystem default.
        # Kaggle executes raw source without __file__,
        # and EmbeddedV7OpeningBook never uses it.
        if stripped.startswith("DEFAULT_BOOK ="):
            skipping_default_book = True
            continue

        if skipping_default_book:
            if stripped == ")":
                skipping_default_book = False
            continue

        if stripped.startswith(
            "from src."
        ):
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

        line = line.replace(
            "path=DEFAULT_BOOK",
            "path=None",
        )

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


def build_v6_base():
    """
    Generate the exact existing V6.1 submission
    using its proven builder.
    """

    subprocess.run(
        [
            sys.executable,
            str(V6_BUILDER),
        ],
        cwd=ROOT,
        check=True,
    )

    return OUTPUT_FILE.read_text()


def build_v7_payload():
    raw = V7_BOOK_FILE.read_bytes()

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


def main():
    # ========================================================
    # BUILD PROVEN V6.1 BASE
    # ========================================================

    submission = build_v6_base()

    # ========================================================
    # READ V7 BOOK READER
    # ========================================================

    v7_book_code = clean_module(
        V7_BOOK_READER_FILE.read_text()
    )

    # ========================================================
    # EMBED V7 DEPTH-12 SCORE BOOK
    # ========================================================

    (
        v7_raw,
        v7_compressed,
        v7_encoded,
    ) = build_v7_payload()

    v7_literal = wrap_encoded(
        v7_encoded
    )

    v7_section = f'''
# ============================================================
# V7.1 DEPTH-12 EXACT SCORE BOOK
# ============================================================

V7_BOOK_DATA_B85 = (
{v7_literal}
)

_V7_BOOK_RAW = None


def _load_v7_book_raw():
    global _V7_BOOK_RAW

    if _V7_BOOK_RAW is None:
        compressed = base64.b85decode(
            V7_BOOK_DATA_B85.encode(
                "ascii"
            )
        )

        _V7_BOOK_RAW = lzma.decompress(
            compressed
        )

    return _V7_BOOK_RAW


# ============================================================
# V7 BOOK READER
# ============================================================

{v7_book_code}


class EmbeddedV7OpeningBook(
    V7OpeningBook
):
    """
    V7OpeningBook backed entirely by the
    book embedded in this submission.
    """

    def __init__(self):
        self.path = None

        self.data = (
            _load_v7_book_raw()
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


V7_BOOK = EmbeddedV7OpeningBook()


def v71_exact_book_move(
    p1,
    p2,
    player,
):
    """
    Return an exactly proven optimal move
    when the V7 book contains the parent
    and every required non-terminal child.

    Otherwise return None and allow V6.1
    to handle the position.
    """

    parent_score = V7_BOOK.lookup(
        p1,
        p2,
        player,
    )

    if parent_score is None:
        return None

    legal = valid_moves(
        p1,
        p2,
    )

    if not legal:
        return None

    ply = (
        p1 | p2
    ).bit_count()

    scored = []

    for col in legal:
        n1, n2 = play_move(
            p1,
            p2,
            col,
            player,
        )

        own_position = (
            n1
            if player == 1
            else n2
        )

        # Immediate winning move.
        if has_won(
            own_position
        ):
            score = (
                42
                - ply
                + 1
            ) // 2

            scored.append(
                (
                    col,
                    score,
                )
            )

            continue

        child_score = V7_BOOK.lookup(
            n1,
            n2,
            3 - player,
        )

        # Never override V6.1 unless the
        # whole decision is exactly proven.
        if child_score is None:
            return None

        scored.append(
            (
                col,
                -int(child_score),
            )
        )

    if not scored:
        return None

    best_score = max(
        score
        for _, score in scored
    )

    # Safety check against the exact parent.
    if best_score != int(
        parent_score
    ):
        return None

    best_moves = {{
        col
        for col, score in scored
        if score == best_score
    }}

    for col in CENTER_ORDER:
        if col in best_moves:
            return col

    return None


'''

    # ========================================================
    # INSERT V7 SECTION BEFORE V6 SEARCH SETTINGS
    # ========================================================

    marker = (
        "# ============================================================\n"
        "# V6B SEARCH SETTINGS\n"
        "# ============================================================"
    )

    if marker not in submission:
        raise RuntimeError(
            "Could not find V6 search-settings marker"
        )

    submission = submission.replace(
        marker,
        v7_section
        + marker,
        1,
    )

    # ========================================================
    # INSERT V7.1 OVERRIDE INTO AGENT
    # ========================================================

    old_agent = '''    player = observation.mark

    # --------------------------------------------------------
    # 1. SOLVED OPENING BOOK
    # --------------------------------------------------------

    book_move = book_choose_move(
'''

    new_agent = '''    player = observation.mark

    # --------------------------------------------------------
    # 1. V7.1 EXACT DEPTH-12 OVERRIDE
    # --------------------------------------------------------

    v71_move = v71_exact_book_move(
        p1,
        p2,
        player,
    )

    if v71_move is not None:
        return int(
            v71_move
        )

    # --------------------------------------------------------
    # 2. V6.1 SOLVED OPENING BOOK
    # --------------------------------------------------------

    book_move = book_choose_move(
'''

    if old_agent not in submission:
        raise RuntimeError(
            "Could not find V6 agent insertion point"
        )

    submission = submission.replace(
        old_agent,
        new_agent,
        1,
    )

    # Cosmetic labels.
    submission = submission.replace(
        "# ConnectX V6B",
        "# ConnectX V7.1 Hybrid",
        1,
    )

    submission = submission.replace(
        "# 2. EXACT ENDGAME",
        "# 3. EXACT ENDGAME",
        1,
    )

    submission = submission.replace(
        "# 3. TIMED MIDDLEGAME SEARCH",
        "# 4. TIMED MIDDLEGAME SEARCH",
        1,
    )

    # ========================================================
    # WRITE FINAL V7.1 SUBMISSION
    # ========================================================

    OUTPUT_FILE.write_text(
        submission
    )

    print()
    print("=" * 60)
    print("CONNECTX V7.1 HYBRID")
    print("=" * 60)

    print(
        "Generated:",
        OUTPUT_FILE,
    )

    print(
        "V7 raw book:",
        f"{len(v7_raw) / 1024**2:.2f} MB",
    )

    print(
        "V7 compressed:",
        f"{len(v7_compressed) / 1024**2:.2f} MB",
    )

    print(
        "V7 encoded:",
        f"{len(v7_encoded) / 1024**2:.2f} MB",
    )

    print(
        "Final submission:",
        f"{OUTPUT_FILE.stat().st_size / 1024**2:.2f} MB",
    )

    print("=" * 60)


if __name__ == "__main__":
    main()