# ConnectX Autonomous Game Agent

A high-performance autonomous Connect Four agent developed for the Kaggle ConnectX competition.

The project explores how an intelligent agent can make decisions under strict time constraints using **adversarial planning, Minimax-style search, alpha-beta pruning, state memory, solved knowledge, exact search, and automated evaluation**.

Rather than selecting moves from fixed rules, the agent evaluates the current state, models possible opponent responses, searches future trajectories, reuses previously solved states, and autonomously selects an action designed to maximize the game-theoretic outcome.

## Intelligent Agent Concepts

ConnectX implements several foundational ideas in autonomous decision-making and classical AI.

### Adversarial Planning

The engine uses **Negamax**, a simplified formulation of Minimax, to model both its own future actions and the opponent's responses.

Each candidate move creates a future game state, which creates another set of possible actions and counter-actions. The agent recursively searches this game tree before committing to a move.

### Alpha-Beta Pruning

Searching every possible future game state is computationally infeasible under Kaggle's runtime constraints.

**Alpha-beta pruning** allows the agent to eliminate branches that cannot influence the final decision, enabling substantially deeper planning without changing the theoretical result of the search.

### Principal Variation Search

V6 extends alpha-beta search with **Principal Variation Search (PVS)**.

The engine predicts the most promising continuation and searches that principal variation first. Alternative moves can then be tested using narrower search windows, reducing unnecessary exploration when move ordering is accurate.

### Time-Bounded Decision Making

The agent uses **iterative deepening** to progressively increase planning depth.

This creates an anytime decision process:

```text
depth 1
   ↓
depth 2
   ↓
depth 3
   ↓
...
   ↓
time budget reached
   ↓
return deepest fully completed decision
```

If search is interrupted by the runtime limit, the agent retains the result from the deepest fully completed iteration rather than returning an incomplete search result.

### State Memory

A **transposition table** acts as search memory.

Different action sequences can reach identical game states. Instead of analyzing those states repeatedly, the engine caches previous search results and reuses them when the same position appears elsewhere in the search tree.

### Knowledge Retrieval

The agent also uses a large solved opening book.

When the current state matches previously solved knowledge, the engine can retrieve the appropriate action immediately rather than recomputing the position from scratch.

### Multi-Step Prediction

The engine records its **principal variation**, representing its predicted best sequence of future actions for both itself and its opponent.

This makes it possible to inspect not only what move the agent chooses, but what it expects the opponent to do next and how it plans to respond.

## V6 Architecture

The current engine uses a layered decision pipeline:

```text
Current Board State
        |
        v
+-----------------------+
| Immediate Tactics     |
| Win / Forced Block    |
+-----------+-----------+
            |
            v
+-----------------------+
| Solved Opening Book   |
| ~1.2M positions       |
+-----------+-----------+
            |
            v
+-----------------------+
| Middlegame Search     |
| Negamax               |
| Alpha-Beta            |
| PVS                   |
| Iterative Deepening   |
| Transposition Table   |
+-----------+-----------+
            |
            v
+-----------------------+
| Exact Endgame Search  |
| <= 23 empty cells     |
+-----------+-----------+
            |
            v
        Selected Move
```

## Opening Knowledge

V6 uses a solved opening book containing approximately **1.2 million positions**.

The book is compressed and embedded into the standalone Kaggle submission.

Lookup is horizontal-symmetry aware, allowing mirrored positions to share solved knowledge and reducing redundant storage.

This provides strong early-game decisions without consuming the move's search budget.

## Middlegame Search

Positions outside solved opening coverage are handled by a bitboard search engine implementing:

- Negamax / Minimax-style adversarial search
- Alpha-beta pruning
- Principal Variation Search
- Iterative deepening
- Transposition tables
- Immediate win detection
- Forced-block detection
- Non-losing move pruning
- Gravity-aware threat detection
- Tactical move ordering
- Time-controlled search

The engine uses a compact bitboard representation with seven bits per column to make board operations and tactical checks efficient.

## Exact Endgame Search

Late-game positions can switch from heuristic depth-limited search to direct **exact-to-terminal search**.

The current endgame solver activates with **23 or fewer empty cells**.

Instead of asking whether a position appears favorable at a search horizon, exact search attempts to determine the actual game-theoretic result.

## Automated Evaluation

A major part of the project became evaluating the agent rather than simply adding more heuristics.

The repository contains tooling for:

- V6 vs. baseline tournaments
- A/B engine testing
- Search benchmarks
- Opening-book validation
- Endgame benchmarks
- Regression testing
- Principal-variation analysis
- Real Kaggle episode parsing
- Exact solver comparison
- Root move-ordering experiments
- Game-theoretic oracle analysis

## Pascal Pons Solver Oracle

Real V6 decisions are compared against the Pascal Pons Connect Four solver.

For each position, the oracle determines the exact score of every legal move and checks whether V6 selected a game-theoretically optimal action.

Moves can then be classified by their effect on the theoretical result:

```text
WIN  -> WIN
WIN  -> DRAW
WIN  -> LOSS

DRAW -> DRAW
DRAW -> LOSS

LOSS -> LOSS
```

This provides a stronger evaluation signal than win rate alone.

A move can therefore be identified as a critical mistake even if V6 later wins because the opponent fails to exploit it.

## Real Kaggle Evaluation

A dataset of **56 analyzable V6.1 Kaggle games** was evaluated using the solver oracle.

Across **1,072 V6 decisions**:

- **1,019** were Pascal Pons-best decisions
- **95.1%** Pons-best move rate
- **1,038** preserved the game-theoretic result
- **96.8%** outcome-preserving rate

The oracle identified **34 outcome-changing decisions**:

| Transition | Count |
|---|---:|
| WIN -> DRAW | 16 |
| WIN -> LOSS | 12 |
| DRAW -> LOSS | 6 |
| **Total** | **34** |

## Discovering the Main Failure Region

One of the most useful findings came from grouping real competition failures by game depth.

Every identified outcome-changing V6 decision occurred between **plies 11 and 18**.

Most were concentrated even earlier:

```text
Ply 11 : 4
Ply 12 : 6
Ply 13 : 5
Ply 14 : 9
Ply 15 : 4
Ply 16 : 3
Ply 17 : 0
Ply 18 : 3
```

**28 of 34 critical mistakes occurred between plies 11 and 15.**

This revealed a specific architectural weakness rather than a general engine failure:

```text
Solved Opening
      |
      | strong
      v
~ Ply 10
      |
      | <-- primary remaining weakness
      |
Ply 11-18
      |
      v
Exact Endgame
      |
      | strong
      v
Terminal State
```

The largest remaining problem is therefore the **bridge between solved opening knowledge and deep exact search**.

## Failure-Driven Development

Real competition mistakes are converted into regression positions.

Oracle analysis discovered positions where V6 converted winning or drawing positions into theoretically worse outcomes.

These positions were isolated, reproduced locally, analyzed at different search depths, and added to regression tests.

This creates an iterative development cycle:

```text
Kaggle Game
     ↓
Episode Analysis
     ↓
Solver Oracle
     ↓
Identify Critical Decision
     ↓
Reproduce Locally
     ↓
Diagnose Search Failure
     ↓
Regression Test
     ↓
Engine Improvement
```

This prevents previously diagnosed failures from silently returning in later versions.

## Search Optimization Experiments

Several search improvements were evaluated through controlled A/B testing.

### Principal Variation Search

PVS reduced the number of nodes required on difficult regression positions while preserving existing correctness tests.

### Root Move Ordering

Experiments demonstrated that search cost can change significantly depending on whether the true principal variation is explored early.

This highlighted the interaction between:

- iterative deepening
- transposition-table move ordering
- principal variation prediction
- alpha-beta efficiency

### Search Depth Analysis

Critical Kaggle positions were searched at increasing depths and compared against exact solver decisions.

Some failures were corrected at approximately depth 15, while others required depth 18 or remained unresolved by heuristic search at that depth.

This demonstrated that the remaining problem could not be solved purely through small parameter adjustments.

## Experimental Exact Solver

The project also includes an experimental Python implementation of a Connect-Four-specific exact solver based on techniques used by Pascal Pons.

It explores:

- Null-window Negamax
- Mathematical game-score bounds
- Non-losing move generation
- Threat-based move ordering
- Bound-based transposition tables
- Exact game-theoretic solving

The implementation successfully reproduced exact Pons results on tested positions.

However, profiling exposed a major performance difference between the Python implementation and an optimized **C++ Connect Four solver**.

Difficult positions that required several seconds or more in the experimental Python implementation could be solved by the optimized C++ solver in tens of milliseconds.

Because Kaggle imposes a strict per-move runtime constraint, future improvements to deep exact solving may benefit from moving performance-critical solving or offline solved-position generation to **C++**.

The experimental Python exact solver is retained for research and validation but is **not currently part of the production V6 decision pipeline**.

## Potential V7 Architecture

Real-game failure analysis suggests a future architecture based on extending solved knowledge through the middlegame bridge:

```text
+-----------------------+
| Solved Opening Book   |
| Early Game            |
+-----------+-----------+
            |
            v
+-----------------------+
| Solved Bridge         |
| Ply ~11-18            |
| Offline C++ Solving   |
+-----------+-----------+
            |
            v
+-----------------------+
| PVS Search Fallback   |
| Python                |
+-----------+-----------+
            |
            v
+-----------------------+
| Exact Endgame Search  |
+-----------------------+
```

One possible direction is to use high-performance C++ solving offline to generate additional solved middlegame positions, compress those results, and embed them into the self-contained Python Kaggle submission.

This would keep runtime lookup inexpensive while moving expensive exact solving outside the competition environment.

## Repository Structure

```text
src/
    bitboard.py
    search.py
    v6_agent.py
    opening_book.py
    exact_solver.py

analysis/
    episode_parser.py
    solver_oracle.py
    v6_game_oracle.py
    pv_analysis.py
    pv_oracle.py
    critical_depth_analysis.py
    root_order_debug.py
    root_order_experiment.py
    ...

benchmarks/
    tournament.py
    v6_ab_tournament.py
    endgame_benchmark.py
    exact_solver_benchmark.py
    ...

tests/
    test_search.py
    test_opening_book.py
    test_compact_book.py
    test_solver_regressions.py

tools/
    build_submission.py
    build_opening_book.py
    build_compact_book.py
```

## Competition Constraints

The production agent is designed around Kaggle ConnectX's environment:

- 7 x 6 Connect Four board
- Four pieces required to win
- Strict per-move runtime budget
- Self-contained Python submission
- No required external runtime files

`tools/build_submission.py` generates the standalone `submission.py` used for competition submission.

## Current Status

V6 established strong solved opening coverage, optimized adversarial search, and exact late-game capabilities.

Large-scale oracle analysis identified the **ply 11-18 middlegame bridge** as the primary remaining weakness.

Development is currently checkpointed at this stage, with future work focused on stronger exact middlegame coverage and potential C++-accelerated offline solving.

## Acknowledgments

Game-theoretic validation and exact-solver research use Pascal Pons' Connect Four solver and its published solving techniques.

The original Pascal Pons Connect Four solver is distributed under the GNU Affero General Public License v3.
