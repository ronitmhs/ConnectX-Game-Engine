# ConnectX Autonomous Game Agent

A high-performance Connect Four agent developed for the Kaggle ConnectX competition.

The project combines **solved game knowledge, adversarial search, exact solving, bitboard optimization, regression testing, and oracle-driven evaluation**. Development progressed from a time-bounded Python search agent to an experimentally perfect solver and finally to a Kaggle-compatible hybrid that incorporates deeper exact knowledge while retaining the proven search fallback.

## Current Agent: V7.1 Hybrid

V7.1 is the current Kaggle-compatible agent.

Its decision pipeline is:

```text
Current Position
      |
      v
+---------------------------+
| V7 Depth-12 Exact Book    |
| 9,188,816 solved states   |
+-------------+-------------+
              |
              | Can the move be
              | proven exactly?
              v
        Yes ------> Play exact move
              |
              No
              v
+---------------------------+
| V6.1 Fallback             |
|                           |
| Solved opening book       |
| PVS / alpha-beta search   |
| Transposition table       |
| Exact endgame search      |
+-------------+-------------+
              |
              v
         Selected Move
```

The V7.1 override is intentionally conservative. It replaces V6.1's decision only when the depth-12 book contains enough information to prove the complete move decision exactly. Otherwise, the agent falls back to the existing V6.1 engine.

This preserves the behavior of the established Kaggle-compatible agent while correcting positions where deeper solved knowledge can demonstrate a better move.

## V7.1 vs V6.1

V7.1 was compared against V6.1 using positions with independently verified perfect-solver results.

On 49 real positions where the V7.1 exact-book override had complete coverage:

| Agent | Optimal Decisions |
|---|---:|
| V6.1 | 44 / 49 — 89.80% |
| V7.1 | **49 / 49 — 100.00%** |

V7.1 corrected **5 demonstrated V6.1 mistakes** in this set.

```text
V7.1 improvements: 5
V7.1 regressions:  0
```

Outside exactly proven V7.1 positions, the engine falls back to V6.1.

## Experimental V7 Perfect Solver

Before V7.1, the project developed a substantially stronger V7 exact solver.

V7 combines:

- A 9,188,816-position depth-12 exact opening book
- Bitboard game representation
- Null-window Negamax
- Alpha-beta pruning
- Mathematical Connect Four score bounds
- Non-losing move pruning
- Threat-based move ordering
- Symmetry-aware transposition tables
- Numba-compiled search

### Independent Perfect-Solver Validation

V7 was tested on **415 unique, non-terminal positions extracted from real Kaggle games**, spanning plies 10 through 24.

The independent Rust perfect solver served as the oracle.

```text
Exact score agreement:  415 / 415 — 100%
Optimal move agreement: 415 / 415 — 100%
Outcome agreement:      415 / 415 — 100%
Errors:                  0
```

Performance on the same set:

```text
Average:  0.0228 s
Median:   0.0021 s
P95:      0.1080 s
P99:      0.2548 s
Maximum:  1.1335 s
> 2 sec:  0
```

Of the 415 decisions:

```text
Book decisions:   76
Exact solves:    339
```

This ensured the validation was not simply measuring opening-book retrieval.

## V7 vs V6.1

V7 and V6.1 were also compared in **830 paired games** starting from 415 distinct real Kaggle positions.

Each starting position was played twice with player assignments reversed.

```text
V7 wins:    402
V6.1 wins:  353
Draws:       75

V7 match score: 52.95%
```

V7 was also substantially faster during this evaluation:

| Metric | V7 | V6.1 |
|---|---:|---:|
| Average move | 0.0034 s | 0.1771 s |
| Median | 0.00013 s | 0.00112 s |
| P95 | 0.0146 s | 1.6554 s |
| P99 | 0.0609 s | 1.6591 s |
| Maximum | 1.0700 s | 1.7016 s |
| Moves > 2 s | 0 | 0 |

## Exact Disagreement Analysis

Head-to-head game results alone can hide decision quality because different moves may preserve the same theoretical outcome.

The tournament therefore recorded every unique position where V7 and V6.1 selected different moves.

This produced **1,507 disagreement positions**, which were independently solved.

```text
V7 optimal:    1507 / 1507 — 100.00%
V6.1 optimal:  1437 / 1507 — 95.36%
```

Decision-quality breakdown:

```text
Both optimal:             1437
V7 optimal, V6.1 not:       70
V6.1 optimal, V7 not:        0
Neither optimal:              0
```

On positions with a theoretically winning outcome:

```text
V7 optimal:    552 / 552 — 100.00%
V6.1 optimal:  513 / 552 — 92.93%
```

This produced the strongest evidence that V7 improved decision quality rather than merely winning more test games.

## Why V7.1 Exists

The full V7 solver is fast enough locally, but Kaggle's submission validator exposed a deployment incompatibility.

The local development environment used:

```text
NumPy 2.3.5
Numba 0.62.1
```

The Kaggle submission validator used a NumPy version incompatible with its installed Numba package, causing Numba to fail during module import before the agent could play.

Instead of weakening the solver or relying on unsupported runtime behavior, V7.1 moves the useful exact knowledge into a pure-Python-compatible deployment architecture:

```text
Offline exact solving
        |
        v
Compressed solved knowledge
        |
        v
Runtime lookup
        |
        +---- exact decision available --> use it
        |
        +---- otherwise -----------------> V6.1
```

The result retains a Kaggle-compatible Python runtime while incorporating exact improvements discovered during V7 development.

## Solved Knowledge

### V6 Opening Book

The V6/V6.1 engine uses a solved opening book containing approximately **1.2 million positions**.

It stores solved opening actions and supports horizontal symmetry to reduce redundant storage.

### V7 Depth-12 Book

V7 introduced a much larger exact score book:

```text
Positions: 9,188,816
Raw compact book: ~20 MB
LZMA compressed:  ~4.6 MB
Base85 embedded:  ~5.8 MB
```

The compact representation uses block-indexed, delta-encoded keys to make millions of solved states practical to embed inside a standalone Python submission.

A benchmark of the block-indexed book produced lookup throughput around:

```text
~21,900 lookups / second
~45.6 microseconds / lookup
```

in the standalone Python reader benchmark.

## V6.1 Search Engine

When exact solved knowledge is unavailable, V7.1 retains the V6.1 search engine.

The engine includes:

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
- Exact late-game search

The board uses a compact seven-bits-per-column bitboard representation.

## Exact Endgame Search

V6.1 can switch from heuristic depth-limited search to direct exact-to-terminal search in sufficiently late positions.

The production cutoff is currently:

```text
23 or fewer empty cells
```

If exact solving cannot complete within its time budget, the engine retains a safe fallback rather than returning an incomplete search result.

## Failure-Driven Development

A major part of this project is the evaluation pipeline rather than only the search algorithm.

Real competition failures are converted into reproducible regression positions:

```text
Kaggle Game
     |
     v
Episode Analysis
     |
     v
Perfect-Solver Oracle
     |
     v
Critical Decision
     |
     v
Local Reproduction
     |
     v
Regression Test
     |
     v
Engine Improvement
```

This process exposed the main V6 weakness around the transition between solved opening knowledge and deeper search.

Earlier analysis found that all identified outcome-changing V6 decisions occurred between approximately **plies 11 and 18**, with most concentrated near the beginning of that interval.

That observation directly motivated the deeper V7 solved book and V7.1 hybrid architecture.

## Testing

The repository includes tests and benchmarks for:

- Bitboard operations
- Opening-book lookup
- Compact-book encoding
- Search behavior
- Historical solver regressions
- V7 book lookup
- V7 regression positions
- Exact-solver benchmarking
- V6 A/B testing
- V7 vs V6.1 tournaments
- Real Kaggle episode analysis
- Perfect-solver oracle comparison
- Submission packaging

Run the test suite with:

```bash
python3 -m pytest tests/ -q
```

## Building the Submission

### V6.1

```bash
python3 tools/build_submission.py
```

### V7.1 Hybrid

```bash
python3 tools/build_submission_v71.py
```

The V7.1 builder:

1. Generates the proven V6.1 standalone submission.
2. Compresses and embeds the V7 depth-12 exact score book.
3. Adds the conservative exact-book decision override.
4. Retains V6.1 as the fallback.
5. Produces a self-contained `submission.py`.

The generated Kaggle submission has no dependency on repository-local `src.*` imports or external book files.

## Repository Structure

```text
src/
    bitboard.py
    search.py
    v6_agent.py

    v7_book.py
    v7_solver.py
    v7_compiled.py
    v7_agent.py
    v71_agent.py

analysis/
    episode_parser.py
    solver_oracle.py
    v6_game_oracle.py
    pv_analysis.py
    critical_depth_analysis.py
    ...

benchmarks/
    tournament.py
    v6_ab_tournament.py
    v7_solver_benchmark.py
    v7_vs_v61.py
    ...

tests/
    test_bitboard.py
    test_search.py
    test_opening_book.py
    test_compact_book.py
    test_solver_regressions.py
    test_v7_book.py
    test_v7_regressions.py

tools/
    build_submission.py
    build_submission_v7.py
    build_submission_v71.py
    build_v7_book.py
    ...

data/
    opening_book/
    v7/
```

## Version Progression

```text
V2–V4
  |
  +-- Early search and tactical agents
  |
 V6
  |
  +-- Solved opening book
  +-- Stronger adversarial search
  |
 V6.1
  |
  +-- PVS
  +-- Exact endgame
  +-- Failure-driven regression improvements
  |
 V7
  |
  +-- 9.19M-position depth-12 exact book
  +-- Compiled perfect solver
  +-- 100% oracle agreement in validation
  |
 V7.1
  |
  +-- Kaggle-compatible hybrid
  +-- Exact V7 book override
  +-- V6.1 fallback
```

## Competition Constraints

The production agent is designed for Kaggle ConnectX:

- 7 × 6 Connect Four board
- Four pieces required to win
- Strict per-action runtime budget
- Self-contained Python source submission
- No required external runtime files

The project deliberately separates **offline computation** from **runtime decision making**. Expensive perfect solving can be performed offline and compressed into solved knowledge, while the competition agent performs inexpensive lookup and bounded search.

## Acknowledgments

Exact Connect Four validation and solver research were informed by Pascal Pons' Connect Four solving techniques.

The project also used the open-source `connect-four-ai` Rust implementation by Benjamin Rall for independent exact-solver validation and depth-12 solved-book research.

Third-party solver code and data remain subject to their respective licenses. This repository's own code should be interpreted separately from those upstream projects and datasets.