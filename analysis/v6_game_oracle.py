import json
from pathlib import Path

from analysis.solver_oracle import (
    solver_analyze,
    best_solver_moves,
)


EPISODE_DIR = Path("data/episodes_v6_1")
OUR_NAME = "Ronit Shah"


def classify(score):
    if score > 0:
        return "WIN"

    if score == 0:
        return "DRAW"

    return "LOSS"


def get_v6_index(episode):
    """
    Identify our player index.

    Skip self-play episodes where both agents have
    the same name because the side is ambiguous.
    """

    names = episode["info"]["TeamNames"]

    matches = [
        i
        for i, name in enumerate(names)
        if name == OUR_NAME
    ]

    if len(matches) != 1:
        return None

    return matches[0]


def extract_game(episode):
    """
    Reconstruct the complete move sequence and return
    every position immediately before an actual V6 move.
    """

    our_index = get_v6_index(episode)

    if our_index is None:
        return None

    names = episode["info"]["TeamNames"]
    rewards = episode["rewards"]

    opponent_index = 1 - our_index

    our_player = our_index + 1
    opponent = names[opponent_index]

    reward = rewards[our_index]

    if reward == 1:
        result = "WIN"
    elif reward == -1:
        result = "LOSS"
    else:
        result = "DRAW"

    steps = episode["steps"]

    sequence = ""
    decisions = []

    # At step i, the board represents the position after
    # i moves. The action that produces the next position
    # is stored in the next state for the player who moved.
    for step_index in range(
        len(steps) - 1
    ):
        states = steps[step_index]

        player_to_move = (
            1
            if step_index % 2 == 0
            else 2
        )

        player_index = (
            player_to_move - 1
        )

        next_state = (
            steps[step_index + 1][player_index]
        )

        move = next_state.get("action")

        if move is None:
            continue

        if player_to_move == our_player:
            decisions.append({
                "ply": step_index,
                "sequence": sequence,
                "actual_move": int(move),
            })

        sequence += str(
            int(move) + 1
        )

    return {
        "episode_id":
            episode["info"]["EpisodeId"],
        "opponent":
            opponent,
        "our_player":
            our_player,
        "result":
            result,
        "sequence":
            sequence,
        "decisions":
            decisions,
    }


def analyze_decision(decision):
    sequence = decision["sequence"]
    move = decision["actual_move"]

    scores = solver_analyze(
        sequence
    )

    best_score, best_moves = (
        best_solver_moves(
            scores
        )
    )

    chosen_score = scores[move]

    before = classify(
        best_score
    )

    after = classify(
        chosen_score
    )

    return {
        **decision,
        "scores":
            scores,
        "best_score":
            best_score,
        "best_moves":
            best_moves,
        "chosen_score":
            chosen_score,
        "optimal":
            move in best_moves,
        "before":
            before,
        "after":
            after,
    }


def main():
    paths = sorted(
        EPISODE_DIR.glob("*.json")
    )

    print("=" * 72)
    print("V6 REAL KAGGLE GAME ORACLE")
    print("=" * 72)

    print(
        "Files:",
        len(paths),
    )

    print()

    games = []

    skipped = []

    for path in paths:
        with path.open() as f:
            episode = json.load(f)

        game = extract_game(
            episode
        )

        if game is None:
            skipped.append(
                path.name
            )
            continue

        games.append(game)

    print(
        "Analyzable games:",
        len(games),
    )

    print(
        "Skipped ambiguous/self-play:",
        len(skipped),
    )

    if skipped:
        for name in skipped:
            print(
                "  ",
                name,
            )

    print()

    wins = sum(
        game["result"] == "WIN"
        for game in games
    )

    losses = sum(
        game["result"] == "LOSS"
        for game in games
    )

    draws = sum(
        game["result"] == "DRAW"
        for game in games
    )

    print(
        f"Results: "
        f"{wins}W / "
        f"{losses}L / "
        f"{draws}D"
    )

    print()

    total_decisions = 0
    optimal_decisions = 0
    outcome_safe = 0

    transitions = {}

    critical = []

    for game in games:
        print("=" * 72)

        print(
            f"Episode {game['episode_id']} "
            f"vs {game['opponent']}"
        )

        print(
            f"Result: {game['result']} | "
            f"V6 player: {game['our_player']}"
        )

        print("=" * 72)

        for decision in game["decisions"]:
            result = analyze_decision(
                decision
            )

            total_decisions += 1

            if result["optimal"]:
                optimal_decisions += 1

            transition = (
                result["before"],
                result["after"],
            )

            transitions[transition] = (
                transitions.get(
                    transition,
                    0,
                )
                + 1
            )

            if (
                result["before"]
                == result["after"]
            ):
                outcome_safe += 1

            is_critical = (
                transition
                in {
                    ("WIN", "DRAW"),
                    ("WIN", "LOSS"),
                    ("DRAW", "LOSS"),
                }
            )

            if is_critical:
                critical.append({
                    "episode":
                        game["episode_id"],
                    "opponent":
                        game["opponent"],
                    **result,
                })

            status = (
                "BEST"
                if result["optimal"]
                else (
                    "CRITICAL"
                    if is_critical
                    else "SAFE"
                )
            )

            print()

            print(
                f"Ply {result['ply']:2} | "
                f"V6 -> {result['actual_move']} | "
                f"{status}"
            )

            print(
                "  Sequence:",
                result["sequence"]
                or "EMPTY",
            )

            print(
                "  Solver scores:",
                result["scores"],
            )

            print(
                "  Solver best:",
                result["best_moves"],
                "| score:",
                result["best_score"],
            )

            print(
                "  V6 score:",
                result["chosen_score"],
            )

            print(
                "  Outcome:",
                f"{result['before']} "
                f"-> {result['after']}",
            )

    print()
    print("=" * 72)
    print("OVERALL SUMMARY")
    print("=" * 72)

    print(
        "Games analyzed:",
        len(games),
    )

    print(
        "V6 decisions:",
        total_decisions,
    )

    print(
        "Pons-best decisions:",
        optimal_decisions,
    )

    if total_decisions:
        print(
            "Pons-best rate:",
            f"{100 * optimal_decisions / total_decisions:.1f}%",
        )

        print(
            "Outcome-preserving:",
            outcome_safe,
        )

        print(
            "Outcome-preserving rate:",
            f"{100 * outcome_safe / total_decisions:.1f}%",
        )

    print()
    print("TRANSITIONS")
    print()

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
        print(
            f"{transition[0]:4} -> "
            f"{transition[1]:4}: "
            f"{transitions.get(transition, 0)}"
        )

    print()
    print("=" * 72)
    print("CRITICAL V6 MISTAKES")
    print("=" * 72)

    print(
        "Count:",
        len(critical),
    )

    for item in critical:
        print()

        print(
            f"Episode {item['episode']} "
            f"vs {item['opponent']}"
        )

        print(
            "Ply:",
            item["ply"],
        )

        print(
            "Sequence:",
            item["sequence"]
            or "EMPTY",
        )

        print(
            "V6 move:",
            item["actual_move"],
        )

        print(
            "Pons-best:",
            item["best_moves"],
        )

        print(
            "Scores:",
            item["best_score"],
            "->",
            item["chosen_score"],
        )

        print(
            "Transition:",
            f"{item['before']} "
            f"-> {item['after']}",
        )


if __name__ == "__main__":
    main()