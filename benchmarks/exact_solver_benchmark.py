import time

from src.exact_solver import (
    ExactSolver,
    from_bitboards,
)

from tests.test_solver_regressions import (
    position_from_sequence,
)


TESTS = [
    {
        "sequence": "444443333147",
        "pons_score": 1,
        "pons_moves": {5},
    },
    {
        "sequence": "436333444467",
        "pons_score": 6,
        "pons_moves": {2, 5},
    },
    {
        "sequence": "44444432655555",
        "pons_score": 1,
        "pons_moves": {2},
    },
]


def main():
    print("=" * 76)
    print("PYTHON PONS-STYLE EXACT SOLVER")
    print("=" * 76)

    all_passed = True

    for item in TESTS:
        sequence = item["sequence"]

        p1, p2, player = (
            position_from_sequence(
                sequence
            )
        )

        position = from_bitboards(
            p1,
            p2,
            player,
        )

        solver = ExactSolver(
            time_limit=30.0
        )

        start = time.perf_counter()

        try:
            score, moves, scores = (
                solver.best_moves(
                    position
                )
            )

        except Exception as exc:
            elapsed = (
                time.perf_counter()
                - start
            )

            print()
            print("-" * 76)

            print(
                "Sequence:",
                sequence,
            )

            print(
                "ERROR:",
                type(exc).__name__,
                str(exc),
            )

            print(
                "Nodes:",
                solver.nodes,
            )

            print(
                "TT hits:",
                solver.tt_hits,
            )

            print(
                "Time:",
                f"{elapsed:.4f}s",
            )

            all_passed = False

            continue

        elapsed = (
            time.perf_counter()
            - start
        )

        expected_score = (
            item["pons_score"]
        )

        expected_moves = (
            item["pons_moves"]
        )

        score_correct = (
            score == expected_score
        )

        moves_correct = (
            set(moves)
            == expected_moves
        )

        passed = (
            score_correct
            and moves_correct
        )

        all_passed &= passed

        print()
        print("-" * 76)

        print(
            "Sequence:",
            sequence,
        )

        print(
            "Player:",
            player,
        )

        print(
            "Scores:",
            scores,
        )

        print(
            "Best score:",
            score,
        )

        print(
            "Best moves:",
            moves,
        )

        print(
            "Expected score:",
            expected_score,
        )

        print(
            "Expected moves:",
            sorted(
                expected_moves
            ),
        )

        print(
            "Score correct:",
            score_correct,
        )

        print(
            "Moves correct:",
            moves_correct,
        )

        print(
            "Nodes:",
            solver.nodes,
        )

        print(
            "TT hits:",
            solver.tt_hits,
        )

        print(
            "TT size:",
            len(solver.tt),
        )

        print(
            "Time:",
            f"{elapsed:.4f}s",
        )

        print(
            "PASS"
            if passed
            else "FAIL"
        )

    print()
    print("=" * 76)

    if all_passed:
        print(
            "FINAL: ALL EXACT TESTS PASS"
        )
    else:
        print(
            "FINAL: EXACT SOLVER NEEDS WORK"
        )

    print("=" * 76)


if __name__ == "__main__":
    main()