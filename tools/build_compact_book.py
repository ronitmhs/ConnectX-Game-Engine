import argparse
import struct
from pathlib import Path

from src.bitboard import play_move


INVALID_SCORE = -1000

RECORD = struct.Struct("<QQbB")


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


def parse_line(line):
    parts = line.strip().split()

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

    return sequence, scores


def best_score_and_mask(scores):
    legal = [
        (col, score)
        for col, score in enumerate(scores)
        if score != INVALID_SCORE
    ]

    if not legal:
        return None, 0

    best_score = max(
        score for _, score in legal
    )

    mask = 0

    for col, score in legal:
        if score == best_score:
            mask |= 1 << col

    return best_score, mask


def build(depth):
    input_file = Path(
        f"data/opening_book/solved_d{depth}.txt"
    )

    output_file = Path(
        f"data/opening_book/book_d{depth}.bin"
    )

    if not input_file.exists():
        raise FileNotFoundError(input_file)

    count = 0

    with input_file.open() as source, \
            output_file.open("wb") as output:

        for line in source:
            if not line.strip():
                continue

            sequence, scores = parse_line(line)

            p1, p2, _ = sequence_to_position(
                sequence
            )

            best_score, move_mask = (
                best_score_and_mask(scores)
            )

            if best_score is None:
                continue

            output.write(
                RECORD.pack(
                    p1,
                    p2,
                    best_score,
                    move_mask,
                )
            )

            count += 1

    size = output_file.stat().st_size

    print("Depth:", depth)
    print("Records:", count)
    print("Record size:", RECORD.size, "bytes")
    print(
        "File size:",
        round(size / (1024 * 1024), 3),
        "MB",
    )

    expected = count * RECORD.size

    print("Expected bytes:", expected)
    print("Actual bytes:", size)

    if expected != size:
        raise RuntimeError(
            "Binary file size mismatch"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--depth",
        required=True,
        type=int,
    )

    args = parser.parse_args()

    build(args.depth)


if __name__ == "__main__":
    main()