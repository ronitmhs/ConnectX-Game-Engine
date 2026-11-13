import time

from tests.test_solver_regressions import (
    position_from_sequence,
)

from src.search import SearchEngine


POSITIONS = [
    {
        "name": "126638838",
        "sequence": "444443333147",
        "pons_moves": {5},
        "transition": "WIN -> LOSS",
    },
    {
        "name": "126639051",
        "sequence": "436333444467",
        "pons_moves": {2, 5},
        "transition": "WIN -> DRAW",
    },
    {
        "name": "126639482",
        "sequence": "44444432655555",
        "pons_moves": {2},
        "transition": "WIN -> DRAW",
    },
]


def analyze_position(item):
    sequence = item["sequence"]
    pons_moves = item["pons_moves"]

    p1, p2, player = (
        position_from_sequence(
            sequence
        )
    )

    print()
    print("=" * 76)
    print(
        f"EPISODE {item['name']} | "
        f"{item['transition']}"
    )
    print("=" * 76)

    print(
        "Sequence:",
        sequence,
    )

    print(
        "Pons moves:",
        sorted(pons_moves),
    )

    print()

    first_correct_depth = None

    for depth in range(6, 19):
        engine = SearchEngine(
            time_limit=10.0
        )

        start = time.perf_counter()

        move = engine.choose_move(
            p1,
            p2,
            player,
            max_depth=depth,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        correct = (
            move in pons_moves
        )

        if (
            correct
            and first_correct_depth is None
        ):
            first_correct_depth = depth

        print(
            f"depth={depth:2} | "
            f"move={move} | "
            f"completed={engine.completed_depth:2} | "
            f"nodes={engine.nodes:7} | "
            f"TT={engine.tt_hits:6} | "
            f"time={elapsed:.4f}s | "
            f"{'PONS' if correct else 'WRONG'}"
        )

    print()

    print(
        "First Pons depth:",
        first_correct_depth,
    )


def main():
    print("=" * 76)
    print("V6.1 REAL-GAME CRITICAL DEPTH ANALYSIS")
    print("=" * 76)

    for item in POSITIONS:
        analyze_position(item)


if __name__ == "__main__":
    main()