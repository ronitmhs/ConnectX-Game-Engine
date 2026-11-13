import subprocess


SOLVER = "tools/connect4/c4solver"
BOOK = "tools/connect4/7x6.book"


POSITIONS = [
    "436333444467",
    "44444432655555",
]


def solver_scores(sequence):
    result = subprocess.run(
        [
            SOLVER,
            "-b",
            BOOK,
            "-a",
        ],
        input=sequence + "\n",
        text=True,
        capture_output=True,
        check=True,
    )

    line = result.stdout.strip()

    parts = line.split()

    if sequence:
        scores = list(
            map(int, parts[1:])
        )
    else:
        scores = list(
            map(int, parts)
        )

    if len(scores) != 7:
        raise ValueError(
            f"Unexpected solver output: {line}"
        )

    return scores


def best_moves(scores):
    legal = [
        (score, col)
        for col, score in enumerate(scores)
        if score != -1000
    ]

    best_score = max(
        score
        for score, _ in legal
    )

    moves = [
        col
        for score, col in legal
        if score == best_score
    ]

    return best_score, moves


def choose_pv_move(scores):
    score, moves = best_moves(scores)

    # Deterministic tie-breaking for diagnostics:
    # prefer center-most among equal solver moves.
    move = min(
        moves,
        key=lambda col: (
            abs(3 - col),
            col,
        ),
    )

    return score, moves, move


def walk_pv(
    start_sequence,
    max_plies=24,
):
    sequence = start_sequence

    print()
    print("=" * 78)
    print(
        "START:",
        start_sequence,
    )
    print("=" * 78)

    for index in range(max_plies):
        scores = solver_scores(
            sequence
        )

        score, moves, move = (
            choose_pv_move(scores)
        )

        side = (
            "ROOT"
            if index % 2 == 0
            else "OPP"
        )

        print()
        print(
            f"PV {index:2} | "
            f"{side:4} | "
            f"position={sequence}"
        )

        print(
            "scores:",
            scores,
        )

        print(
            "best score:",
            score,
        )

        print(
            "best moves:",
            moves,
        )

        print(
            "chosen:",
            move,
            f"(Pons column {move + 1})",
        )

        sequence += str(
            move + 1
        )

        # Large positive/negative values close to terminal
        # will naturally collapse as the PV progresses.
        # Stop if no legal continuation remains.
        try:
            next_scores = solver_scores(
                sequence
            )
        except Exception:
            break

        if all(
            value == -1000
            for value in next_scores
        ):
            break


def main():
    print("=" * 78)
    print("PASCAL PONS FORCED-WIN PV ANALYSIS")
    print("=" * 78)

    for sequence in POSITIONS:
        walk_pv(sequence)


if __name__ == "__main__":
    main()