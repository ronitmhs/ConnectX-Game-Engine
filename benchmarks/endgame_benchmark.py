import json
import time
from pathlib import Path

from src.bitboard import board_to_bitboards
from src.search import SearchEngine


EPISODE_DIR = Path("data/episodes")


def get_positions():
    positions = []

    for path in EPISODE_DIR.glob("*.json"):
        with path.open() as f:
            episode = json.load(f)

        for step in episode["steps"]:
            for agent_state in step:
                obs = agent_state.get("observation", {})

                board = obs.get("board")
                mark = obs.get("mark")

                if not board or mark not in (1, 2):
                    continue

                filled = sum(
                    1 for cell in board if cell
                )

                empties = 42 - filled

                # Endgame positions only
                if empties == 23:
                    positions.append(
                        (
                            empties,
                            board,
                            mark,
                            path.stem,
                        )
                    )

    return positions


def benchmark_position(
    board,
    mark,
    empties,
):
    p1, p2 = board_to_bitboards(board)

    engine = SearchEngine(
        time_limit=10.0
    )

    start = time.perf_counter()

    move = engine.choose_move_exact(
        p1,
        p2,
        mark,
        depth=empties,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    solved = move is not None

    return {
        "move": move,
        "time": elapsed,
        "nodes": engine.nodes,
        "depth": engine.completed_depth,
        "solved": solved,
    }


def main():
    positions = get_positions()

    print(
        "Candidate endgame positions:",
        len(positions),
    )

    print()

    for empties in [23]:
        candidates = [
            p
            for p in positions
            if p[0] == empties
        ]

        # Keep this first experiment quick.
        candidates = candidates[:30]

        if not candidates:
            continue

        times = []
        nodes = []
        solved_count = 0

        print("=" * 60)
        print(
            f"EMPTY CELLS: {empties}"
        )
        print("=" * 60)

        for (
            _,
            board,
            mark,
            episode,
        ) in candidates:

            result = benchmark_position(
                board,
                mark,
                empties,
            )

            times.append(
                result["time"]
            )

            nodes.append(
                result["nodes"]
            )

            if result["solved"]:
                solved_count += 1

            print(
                f"{episode} | "
                f"time={result['time']:.4f}s | "
                f"depth={result['depth']} | "
                f"nodes={result['nodes']} | "
                f"solved={result['solved']}"
            )

        print()
        print(
            f"Solved: {solved_count}/{len(candidates)}"
        )

        print(
            "Average time:",
            f"{sum(times) / len(times):.4f}s",
        )

        print(
            "Worst time:",
            f"{max(times):.4f}s",
        )

        print(
            "Average nodes:",
            int(
                sum(nodes) / len(nodes)
            ),
        )

        print()


if __name__ == "__main__":
    main()