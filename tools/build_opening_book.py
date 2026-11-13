import argparse
import json
from pathlib import Path

from src.bitboard import play_move


INVALID_SCORE = -1000


def sequence_to_position(sequence):
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

    return p1, p2, player


def make_key(p1, p2, player):
    return f"{p1}:{p2}:{player}"


def parse_line(line):
    parts = line.strip().split()

    # Empty-board line contains only the 7 scores.
    if len(parts) == 7:
        sequence = ""
        scores = list(map(int, parts))

    elif len(parts) == 8:
        sequence = parts[0]
        scores = list(map(int, parts[1:]))

    else:
        raise ValueError(
            f"Unexpected line: {line!r}"
        )

    if len(scores) != 7:
        raise ValueError(
            f"Expected 7 scores: {line!r}"
        )

    return sequence, scores


def build_book(depth):
    input_file = Path(
        f"data/opening_book/solved_d{depth}.txt"
    )

    output_file = Path(
        f"data/opening_book/book_d{depth}.json"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Missing input file: {input_file}"
        )

    book = {}

    input_positions = 0

    with input_file.open() as f:
        for line in f:
            if not line.strip():
                continue

            sequence, scores = parse_line(line)

            p1, p2, player = sequence_to_position(
                sequence
            )

            key = make_key(
                p1,
                p2,
                player,
            )

            if key in book:
                raise ValueError(
                    f"Duplicate position key: {key}"
                )

            book[key] = scores
            input_positions += 1

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open("w") as f:
        json.dump(
            book,
            f,
            separators=(",", ":"),
        )

    print("Depth:", depth)
    print("Input file:", input_file)
    print("Output file:", output_file)

    print(
        "Input positions:",
        input_positions,
    )

    print(
        "Book positions:",
        len(book),
    )

    size_mb = (
        output_file.stat().st_size
        / (1024 * 1024)
    )

    print(
        "JSON size:",
        round(size_mb, 3),
        "MB",
    )

    empty_key = make_key(
        0,
        0,
        1,
    )

    scores = book[empty_key]

    print()
    print(
        "Empty-board scores:",
        scores,
    )

    legal = [
        (score, col)
        for col, score in enumerate(scores)
        if score != INVALID_SCORE
    ]

    best_score = max(
        score
        for score, _
        in legal
    )

    best_moves = [
        col
        for score, col in legal
        if score == best_score
    ]

    print(
        "Empty-board best score:",
        best_score,
    )

    print(
        "Empty-board best moves:",
        best_moves,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--depth",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    build_book(args.depth)


if __name__ == "__main__":
    main()