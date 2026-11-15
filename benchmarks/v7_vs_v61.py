import json
import statistics
import time
from pathlib import Path

from src.bitboard import (
    board_to_bitboards,
    has_won,
    play_move,
    valid_moves,
)
from src.v6_agent import (
    choose_move_with_info as v61_choose,
)
from src.v7_agent import (
    choose_move_from_bitboards as v7_choose,
)


EPISODE_DIR = Path("data/episodes")

MIN_PLY = 10
MAX_PLY = 24

TIMEOUT = 2.0


class Observation:
    def __init__(self, board, mark):
        self.board = board
        self.mark = mark


class Configuration:
    rows = 6
    columns = 7
    inarow = 4
    timeout = TIMEOUT


CONFIG = Configuration()


def bitboards_to_board(p1, p2):
    board = [0] * 42

    for r in range(6):
        for c in range(7):
            row_from_bottom = 5 - r

            bit = 1 << (
                c * 7
                + row_from_bottom
            )

            index = r * 7 + c

            if p1 & bit:
                board[index] = 1

            elif p2 & bit:
                board[index] = 2

    return board


def load_starting_positions():
    positions = []
    seen = set()

    for path in sorted(
        EPISODE_DIR.glob("*.json")
    ):
        with path.open() as f:
            episode = json.load(f)

        for step in episode["steps"]:
            board = None

            for state in step:
                candidate = state.get(
                    "observation",
                    {},
                ).get("board")

                if candidate:
                    board = candidate
                    break

            if board is None:
                continue

            ply = sum(
                cell != 0
                for cell in board
            )

            if not (
                MIN_PLY
                <= ply
                <= MAX_PLY
            ):
                continue

            player = (
                1
                if ply % 2 == 0
                else 2
            )

            key = (
                tuple(board),
                player,
            )

            if key in seen:
                continue

            seen.add(key)

            p1, p2 = (
                board_to_bitboards(
                    board
                )
            )

            if (
                has_won(p1)
                or has_won(p2)
            ):
                continue

            positions.append(
                (
                    p1,
                    p2,
                    player,
                    path.stem,
                    ply,
                )
            )

    return positions


def run_v61(
    p1,
    p2,
    player,
):
    board = bitboards_to_board(
        p1,
        p2,
    )

    observation = Observation(
        board,
        player,
    )

    start = time.perf_counter()

    move, info = v61_choose(
        observation,
        CONFIG,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return (
        int(move),
        elapsed,
        info,
    )


def run_v7(
    p1,
    p2,
    player,
):
    start = time.perf_counter()

    move, info = v7_choose(
        p1,
        p2,
        player,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    return (
        int(move),
        elapsed,
        info,
    )


def play_game(
    start_position,
    v7_player,
):
    (
        p1,
        p2,
        player,
        episode,
        starting_ply,
    ) = start_position

    v7_times = []
    v61_times = []

    v7_over_2s = 0
    v61_over_2s = 0

    illegal = None

    disagreements = []

    while True:
        legal = valid_moves(
            p1,
            p2,
        )

        if not legal:
            return {
                "winner": 0,
                "v7_times": v7_times,
                "v61_times": v61_times,
                "v7_over_2s": v7_over_2s,
                "v61_over_2s": v61_over_2s,
                "illegal": illegal,
                "disagreements":
                    disagreements,
            }

        # ----------------------------------------
        # Record what BOTH agents would do
        # before actually playing the assigned
        # agent's move.
        # ----------------------------------------

        v7_move, v7_elapsed, v7_info = (
            run_v7(
                p1,
                p2,
                player,
            )
        )

        (
            v61_move,
            v61_elapsed,
            v61_info,
        ) = run_v61(
            p1,
            p2,
            player,
        )

        if v7_move != v61_move:
            disagreements.append({
                "p1": p1,
                "p2": p2,
                "player": player,
                "ply":
                    (p1 | p2).bit_count(),
                "v7_move": v7_move,
                "v61_move": v61_move,
                "v7_score":
                    v7_info["score"],
                "v7_source":
                    v7_info["source"],
                "episode": episode,
                "starting_ply":
                    starting_ply,
            })

        # Only assigned player's timing counts
        # toward that agent's game statistics.
        if player == v7_player:
            move = v7_move

            v7_times.append(
                v7_elapsed
            )

            if v7_elapsed > TIMEOUT:
                v7_over_2s += 1

        else:
            move = v61_move

            v61_times.append(
                v61_elapsed
            )

            if v61_elapsed > TIMEOUT:
                v61_over_2s += 1

        if move not in legal:
            illegal = (
                "V7"
                if player == v7_player
                else "V6.1"
            )

            return {
                "winner": 3 - player,
                "v7_times": v7_times,
                "v61_times": v61_times,
                "v7_over_2s": v7_over_2s,
                "v61_over_2s": v61_over_2s,
                "illegal": illegal,
                "disagreements":
                    disagreements,
            }

        p1, p2 = play_move(
            p1,
            p2,
            move,
            player,
        )

        played_position = (
            p1
            if player == 1
            else p2
        )

        if has_won(
            played_position
        ):
            return {
                "winner": player,
                "v7_times": v7_times,
                "v61_times": v61_times,
                "v7_over_2s": v7_over_2s,
                "v61_over_2s": v61_over_2s,
                "illegal": illegal,
                "disagreements":
                    disagreements,
            }

        player = 3 - player


def percentile(
    values,
    fraction,
):
    if not values:
        return 0.0

    ordered = sorted(values)

    index = int(
        round(
            (len(ordered) - 1)
            * fraction
        )
    )

    return ordered[index]


def main():
    positions = (
        load_starting_positions()
    )

    print("=" * 78)
    print("V7 EXACT vs V6.1 CURRENT BEST")
    print("=" * 78)

    print(
        "Distinct starting positions:",
        len(positions),
    )

    print(
        "Paired games:",
        len(positions) * 2,
    )

    print(
        "Starting ply range:",
        MIN_PLY,
        "-",
        MAX_PLY,
    )

    print()

    # Warm V7 JIT before timing tournament.
    if positions:
        p1, p2, player, _, _ = (
            positions[0]
        )

        run_v7(
            p1,
            p2,
            player,
        )

    v7_wins = 0
    v61_wins = 0
    draws = 0

    v7_as_p1_wins = 0
    v7_as_p2_wins = 0

    v61_as_p1_wins = 0
    v61_as_p2_wins = 0

    v7_times = []
    v61_times = []

    v7_over_2s = 0
    v61_over_2s = 0

    illegal_moves = []

    disagreement_map = {}

    game_count = 0

    for index, position in enumerate(
        positions,
        start=1,
    ):
        for v7_player in (1, 2):
            game_count += 1

            result = play_game(
                position,
                v7_player,
            )

            v7_times.extend(
                result["v7_times"]
            )

            v61_times.extend(
                result["v61_times"]
            )

            v7_over_2s += (
                result["v7_over_2s"]
            )

            v61_over_2s += (
                result["v61_over_2s"]
            )

            if result["illegal"]:
                illegal_moves.append(
                    (
                        game_count,
                        result["illegal"],
                    )
                )

            for item in (
                result["disagreements"]
            ):
                key = (
                    item["p1"],
                    item["p2"],
                    item["player"],
                )

                disagreement_map[
                    key
                ] = item

            winner = result["winner"]

            if winner == 0:
                draws += 1

            elif winner == v7_player:
                v7_wins += 1

                if v7_player == 1:
                    v7_as_p1_wins += 1
                else:
                    v7_as_p2_wins += 1

            else:
                v61_wins += 1

                if v7_player == 1:
                    v61_as_p2_wins += 1
                else:
                    v61_as_p1_wins += 1

        if (
            index % 25 == 0
            or index == len(positions)
        ):
            print(
                f"{index:3}/"
                f"{len(positions)} positions | "
                f"games={game_count} | "
                f"V7={v7_wins} | "
                f"V6.1={v61_wins} | "
                f"draws={draws}"
            )

    total_games = (
        v7_wins
        + v61_wins
        + draws
    )

    print()
    print("=" * 78)
    print("RESULTS")
    print("=" * 78)

    print()
    print("Games:", total_games)
    print("V7 wins:", v7_wins)
    print("V6.1 wins:", v61_wins)
    print("Draws:", draws)

    v7_score = (
        v7_wins
        + 0.5 * draws
    ) / total_games

    print(
        "V7 match score:",
        f"{v7_score * 100:.2f}%",
    )

    print()
    print("--- BY PLAYER ---")

    print(
        "V7 wins as P1:",
        v7_as_p1_wins,
    )

    print(
        "V7 wins as P2:",
        v7_as_p2_wins,
    )

    print(
        "V6.1 wins as P1:",
        v61_as_p1_wins,
    )

    print(
        "V6.1 wins as P2:",
        v61_as_p2_wins,
    )

    print()
    print("--- V7 TIMING ---")

    if v7_times:
        print(
            "Moves:",
            len(v7_times),
        )

        print(
            "Average:",
            f"{statistics.mean(v7_times):.6f}s",
        )

        print(
            "Median:",
            f"{statistics.median(v7_times):.6f}s",
        )

        print(
            "P95:",
            f"{percentile(v7_times, 0.95):.6f}s",
        )

        print(
            "P99:",
            f"{percentile(v7_times, 0.99):.6f}s",
        )

        print(
            "Maximum:",
            f"{max(v7_times):.6f}s",
        )

        print(
            ">2 seconds:",
            v7_over_2s,
        )

    print()
    print("--- V6.1 TIMING ---")

    if v61_times:
        print(
            "Moves:",
            len(v61_times),
        )

        print(
            "Average:",
            f"{statistics.mean(v61_times):.6f}s",
        )

        print(
            "Median:",
            f"{statistics.median(v61_times):.6f}s",
        )

        print(
            "P95:",
            f"{percentile(v61_times, 0.95):.6f}s",
        )

        print(
            "P99:",
            f"{percentile(v61_times, 0.99):.6f}s",
        )

        print(
            "Maximum:",
            f"{max(v61_times):.6f}s",
        )

        print(
            ">2 seconds:",
            v61_over_2s,
        )

    print()
    print(
        "Illegal moves:",
        len(illegal_moves),
    )

    print(
        "Unique decision disagreements:",
        len(disagreement_map),
    )

    # Save disagreements for exact-oracle
    # analysis after the tournament.
    output = Path(
        "/tmp/v7_v61_disagreements.json"
    )

    with output.open("w") as f:
        json.dump(
            list(
                disagreement_map.values()
            ),
            f,
            indent=2,
        )

    print(
        "Disagreements saved:",
        output,
    )


if __name__ == "__main__":
    main()