import json
import random
from pathlib import Path

from analysis.solver_oracle import (
    solver_analyze,
    best_solver_moves,
)
from src.bitboard import (
    board_to_bitboards,
    play_move,
    has_won,
)
from src.search import SearchEngine


EPISODE_DIR = Path("data/episodes")

SAMPLE_SIZE = 50
MIN_PLY = 11
MAX_PLY = 18
PV_LENGTH = 8
SEARCH_TIME = 1.65
SEED = 42


def classify(score):
    if score > 0:
        return "WIN"
    if score == 0:
        return "DRAW"
    return "LOSS"


def load_positions():
    positions = []
    seen = set()

    for path in sorted(
        EPISODE_DIR.glob("*.json")
    ):
        with path.open() as f:
            episode = json.load(f)

        opponent = "unknown"
        agents = (
            episode
            .get("info", {})
            .get("Agents", [])
        )

        for agent in agents:
            name = agent.get("Name")

            if (
                name
                and name != "Ronit Shah"
            ):
                opponent = name
                break

        for step in episode["steps"]:
            board = None
            mark = None

            for state in step:
                obs = state.get(
                    "observation",
                    {}
                )

                candidate = obs.get(
                    "board"
                )

                candidate_mark = obs.get(
                    "mark"
                )

                if (
                    candidate
                    and candidate_mark in (1, 2)
                ):
                    board = candidate
                    mark = candidate_mark
                    break

            if board is None:
                continue

            ply = sum(
                bool(cell)
                for cell in board
            )

            if not (
                MIN_PLY <= ply <= MAX_PLY
            ):
                continue

            # The side to move is determined by parity.
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

            positions.append({
                "p1": p1,
                "p2": p2,
                "player": player,
                "ply": ply,
                "episode": path.stem,
                "opponent": opponent,
            })

    rng = random.Random(SEED)
    rng.shuffle(positions)

    return positions[:SAMPLE_SIZE]


def sequence_from_bitboards(
    p1,
    p2,
):
    """
    We cannot uniquely reconstruct move order from
    bitboards alone.

    This function intentionally does not attempt it.
    """
    raise RuntimeError(
        "Sequence must be retained while parsing."
    )


def load_positions_with_sequences():
    """
    Reconstruct positions directly from episode actions
    so we retain the exact Pons move sequence.
    """

    positions = []
    seen = set()

    for path in sorted(
        EPISODE_DIR.glob("*.json")
    ):
        with path.open() as f:
            episode = json.load(f)

        sequence = ""

        steps = episode["steps"]

        for index in range(
            1,
            len(steps)
        ):
            previous = steps[index - 1]

            # Find the active player's action from the
            # previous environment step.
            action = None

            for state in previous:
                candidate = state.get(
                    "action"
                )

                status = state.get(
                    "status"
                )

                if (
                    candidate is not None
                    and status == "ACTIVE"
                ):
                    action = candidate
                    break

            # Kaggle episode structure can place the move
            # differently, so derive it from the current
            # board when necessary.
            current_board = None

            for state in steps[index]:
                obs = state.get(
                    "observation",
                    {}
                )

                candidate_board = obs.get(
                    "board"
                )

                if candidate_board:
                    current_board = (
                        candidate_board
                    )
                    break

            if current_board is None:
                continue

            ply = sum(
                bool(cell)
                for cell in current_board
            )

            # Reconstruct sequence from board differences
            # below instead of trusting ACTIVE status.
            if ply == 0:
                sequence = ""
                continue

            # Build sequence from every board encountered
            # by comparing against the prior board.
            previous_board = None

            for state in previous:
                obs = state.get(
                    "observation",
                    {}
                )

                candidate_board = obs.get(
                    "board"
                )

                if candidate_board:
                    previous_board = (
                        candidate_board
                    )
                    break

            if previous_board is not None:
                changed = [
                    i
                    for i, (
                        old,
                        new,
                    ) in enumerate(
                        zip(
                            previous_board,
                            current_board,
                        )
                    )
                    if old != new
                ]

                if len(changed) == 1:
                    col = (
                        changed[0] % 7
                    )

                    if (
                        len(sequence)
                        < ply
                    ):
                        sequence += str(
                            col + 1
                        )

            if not (
                MIN_PLY <= ply <= MAX_PLY
            ):
                continue

            if len(sequence) != ply:
                continue

            player = (
                1
                if ply % 2 == 0
                else 2
            )

            p1, p2 = (
                board_to_bitboards(
                    current_board
                )
            )

            if (
                has_won(p1)
                or has_won(p2)
            ):
                continue

            key = (
                p1,
                p2,
                player,
            )

            if key in seen:
                continue

            seen.add(key)

            positions.append({
                "p1": p1,
                "p2": p2,
                "player": player,
                "ply": ply,
                "sequence": sequence,
                "episode": path.stem,
            })

    rng = random.Random(SEED)
    rng.shuffle(positions)

    return positions[:SAMPLE_SIZE]


def analyze_position(item):
    p1 = item["p1"]
    p2 = item["p2"]
    player = item["player"]
    sequence = item["sequence"]

    engine = SearchEngine(
        time_limit=SEARCH_TIME
    )

    engine.choose_move(
        p1,
        p2,
        player,
    )

    pv = (
        engine.get_principal_variation(
            p1,
            p2,
            player,
            max_length=PV_LENGTH,
        )
    )

    current_sequence = sequence
    current_player = player

    results = []

    for index, move in enumerate(pv):
        scores = solver_analyze(
            current_sequence
        )

        (
            best_score,
            best_moves,
        ) = best_solver_moves(
            scores
        )

        chosen_score = scores[move]

        before = classify(
            best_score
        )

        after = classify(
            chosen_score
        )

        results.append({
            "index": index,
            "player": current_player,
            "move": move,
            "best_moves": best_moves,
            "best_score": best_score,
            "chosen_score": chosen_score,
            "before": before,
            "after": after,
            "optimal": (
                move in best_moves
            ),
            "sequence": current_sequence,
        })

        current_sequence += str(
            move + 1
        )

        current_player = (
            3 - current_player
        )

    return {
        "engine": engine,
        "pv": pv,
        "results": results,
    }


def main():
    positions = (
        load_positions_with_sequences()
    )

    print("=" * 72)
    print("REAL-GAME V6 PV ORACLE DATASET")
    print("=" * 72)

    print(
        "Positions:",
        len(positions),
    )

    print(
        "PV length:",
        PV_LENGTH,
    )

    print()

    total_moves = 0
    optimal_moves = 0
    outcome_safe = 0

    transitions = {}

    critical = []

    for number, item in enumerate(
        positions,
        start=1,
    ):
        result = analyze_position(
            item
        )

        engine = result["engine"]

        print(
            f"{number:2}/{len(positions)} | "
            f"episode={item['episode']} | "
            f"ply={item['ply']} | "
            f"depth={engine.completed_depth} | "
            f"pv={len(result['pv'])}"
        )

        for r in result["results"]:
            total_moves += 1

            if r["optimal"]:
                optimal_moves += 1

            transition = (
                r["before"],
                r["after"],
            )

            transitions[transition] = (
                transitions.get(
                    transition,
                    0,
                )
                + 1
            )

            if (
                r["before"]
                == r["after"]
            ):
                outcome_safe += 1

            if transition in {
                ("WIN", "DRAW"),
                ("WIN", "LOSS"),
                ("DRAW", "LOSS"),
            }:
                critical.append({
                    "episode":
                        item["episode"],
                    "root_ply":
                        item["ply"],
                    **r,
                })

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(
        "PV moves checked:",
        total_moves,
    )

    print(
        "Pons-best moves:",
        optimal_moves,
    )

    if total_moves:
        print(
            "Pons-best rate:",
            f"{100 * optimal_moves / total_moves:.1f}%",
        )

        print(
            "Outcome-preserving:",
            outcome_safe,
        )

        print(
            "Outcome-preserving rate:",
            f"{100 * outcome_safe / total_moves:.1f}%",
        )

    print()
    print("TRANSITIONS")

    order = [
        ("WIN", "WIN"),
        ("WIN", "DRAW"),
        ("WIN", "LOSS"),
        ("DRAW", "WIN"),
        ("DRAW", "DRAW"),
        ("DRAW", "LOSS"),
        ("LOSS", "WIN"),
        ("LOSS", "DRAW"),
        ("LOSS", "LOSS"),
    ]

    for transition in order:
        count = transitions.get(
            transition,
            0,
        )

        print(
            f"{transition[0]:4} -> "
            f"{transition[1]:4}: "
            f"{count}"
        )

    print()
    print("=" * 72)
    print("CRITICAL DEVIATIONS")
    print("=" * 72)

    print(
        "Count:",
        len(critical),
    )

    for c in critical[:20]:
        print()

        print(
            f"Episode {c['episode']} | "
            f"root ply {c['root_ply']} | "
            f"PV index {c['index']}"
        )

        print(
            "Sequence:",
            c["sequence"],
        )

        print(
            "V6 move:",
            c["move"],
        )

        print(
            "Pons-best:",
            c["best_moves"],
        )

        print(
            "Scores:",
            c["best_score"],
            "->",
            c["chosen_score"],
        )

        print(
            "Transition:",
            f"{c['before']} -> "
            f"{c['after']}",
        )


if __name__ == "__main__":
    main()