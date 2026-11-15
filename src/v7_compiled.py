import numpy as np
from numba import njit


ROWS = 6
COLS = 7
BOARD_SIZE = 42
BITS_PER_COL = 7

BOARD_MASK = np.uint64(
    sum(
        ((1 << ROWS) - 1)
        << (col * BITS_PER_COL)
        for col in range(COLS)
    )
)

BOTTOM_MASK = np.uint64(
    sum(
        1 << (col * BITS_PER_COL)
        for col in range(COLS)
    )
)

CENTER_ORDER = np.array(
    [3, 2, 4, 1, 5, 0, 6],
    dtype=np.int64,
)


# ============================================================
# TRANSPOSITION TABLE
# ============================================================

TT_EMPTY = np.uint8(0)
TT_EXACT = np.uint8(1)
TT_LOWER = np.uint8(2)
TT_UPPER = np.uint8(3)

# Match the Rust reference exactly.
#
# Rust:
# MAX_SIZE = (1 << 23) + 9
# index = key % MAX_SIZE
TT_SIZE = (1 << 23) + 9

TT_KEYS = np.zeros(
    TT_SIZE,
    dtype=np.uint32,
)

TT_VALUES = np.zeros(
    TT_SIZE,
    dtype=np.int8,
)

TT_FLAGS = np.zeros(
    TT_SIZE,
    dtype=np.uint8,
)

TT_DEPTHS = np.zeros(
    TT_SIZE,
    dtype=np.uint8,
)

TT_AGES = np.zeros(
    TT_SIZE,
    dtype=np.uint8,
)

TT_AGE = np.zeros(
    1,
    dtype=np.uint8,
)


# ============================================================
# INTEGER HELPERS
# ============================================================

@njit(cache=True)
def trunc_div2(value):
    """
    Match Rust/C/C++ signed integer division.

    Python // floors negative numbers.
    Rust integer division truncates toward zero.
    """

    if value >= 0:
        return value // 2

    return -((-value) // 2)


# ============================================================
# POSITION / SYMMETRY
# ============================================================

@njit(cache=True)
def mirror_bits(value):
    result = np.uint64(0)

    column_mask = np.uint64(
        (1 << BITS_PER_COL) - 1
    )

    for col in range(COLS):
        column = (
            value
            >> np.uint64(
                col * BITS_PER_COL
            )
        ) & column_mask

        result |= (
            column
            << np.uint64(
                (COLS - 1 - col)
                * BITS_PER_COL
            )
        )

    return result


@njit(cache=True)
def position_key(
    current,
    mask,
):
    key = current + mask

    mirrored_key = (
        mirror_bits(current)
        + mirror_bits(mask)
    )

    if mirrored_key < key:
        return mirrored_key

    return key


# ============================================================
# MOVE GENERATION
# ============================================================

@njit(cache=True)
def possible(mask):
    return (
        (mask + BOTTOM_MASK)
        & BOARD_MASK
    )


@njit(cache=True)
def winning_positions(
    position,
    mask,
):
    # Vertical
    result = (
        (position << np.uint64(1))
        & (position << np.uint64(2))
        & (position << np.uint64(3))
    )

    # Horizontal
    p = (
        (position << np.uint64(7))
        & (position << np.uint64(14))
    )

    result |= (
        p
        & (position << np.uint64(21))
    )

    result |= (
        p
        & (position >> np.uint64(7))
    )

    p >>= np.uint64(21)

    result |= (
        p
        & (position << np.uint64(7))
    )

    result |= (
        p
        & (position >> np.uint64(21))
    )

    # Diagonal /
    p = (
        (position << np.uint64(6))
        & (position << np.uint64(12))
    )

    result |= (
        p
        & (position << np.uint64(18))
    )

    result |= (
        p
        & (position >> np.uint64(6))
    )

    p >>= np.uint64(18)

    result |= (
        p
        & (position << np.uint64(6))
    )

    result |= (
        p
        & (position >> np.uint64(18))
    )

    # Diagonal \
    p = (
        (position << np.uint64(8))
        & (position << np.uint64(16))
    )

    result |= (
        p
        & (position << np.uint64(24))
    )

    result |= (
        p
        & (position >> np.uint64(8))
    )

    p >>= np.uint64(24)

    result |= (
        p
        & (position << np.uint64(8))
    )

    result |= (
        p
        & (position >> np.uint64(24))
    )

    return (
        result
        & BOARD_MASK
        & ~mask
    )


@njit(cache=True)
def possible_non_losing(
    current,
    mask,
):
    moves = possible(mask)

    opponent = (
        current ^ mask
    )

    opponent_wins = (
        winning_positions(
            opponent,
            mask,
        )
    )

    forced = (
        moves
        & opponent_wins
    )

    if forced != 0:
        # Two forced blocks means the
        # position is already lost.
        if (
            forced
            & (
                forced
                - np.uint64(1)
            )
        ) != 0:
            return np.uint64(0)

        moves = forced

    # Do not play directly below an
    # opponent winning square.
    return (
        moves
        & ~(
            opponent_wins
            >> np.uint64(1)
        )
        & BOARD_MASK
    )


@njit(cache=True)
def can_win_next(
    current,
    mask,
):
    return (
        winning_positions(
            current,
            mask,
        )
        & possible(mask)
    ) != 0


# ============================================================
# MOVE ORDERING
# ============================================================

@njit(cache=True)
def popcount(value):
    count = 0

    while value:
        value &= (
            value
            - np.uint64(1)
        )

        count += 1

    return count


@njit(cache=True)
def move_score(
    current,
    mask,
    move,
):
    return popcount(
        winning_positions(
            current | move,
            mask,
        )
    )


# ============================================================
# TRANSPOSITION TABLE
# ============================================================

@njit(cache=True)
def tt_index(key):
    """
    Match the Rust reference implementation.

    Rust:
        index = key % MAX_SIZE
    """

    return int(
        key % np.uint64(TT_SIZE)
    )


# ============================================================
# NEGAMAX
# ============================================================

@njit(cache=True)
def negamax(
    current,
    mask,
    moves_played,
    depth,
    alpha,
    beta,
    nodes,
    tt_hits,
    keys,
    values,
    flags,
    depths,
    ages,
    age,
):
    nodes[0] += 1

    if depth == 0:
        return 0

    original_alpha = alpha

    key = position_key(
        current,
        mask,
    )

    index = tt_index(
        key
    )

    # Match Rust's:
    # entry.key = key as u32
    partial_key = np.uint32(
        key
        & np.uint64(
            0xFFFFFFFF
        )
    )

    # --------------------------------------------------------
    # TRANSPOSITION TABLE LOOKUP
    # --------------------------------------------------------

    if (
        ages[index] == age
        and keys[index] == partial_key
        and depths[index] >= depth
    ):
        flag = flags[index]

        value = int(
            values[index]
        )

        tt_hits[0] += 1

        if flag == TT_EXACT:
            return value

        if (
            flag == TT_LOWER
            and value >= beta
        ):
            return value

        if (
            flag == TT_UPPER
            and value <= alpha
        ):
            return value

    # --------------------------------------------------------
    # NON-LOSING MOVE GENERATION
    # --------------------------------------------------------

    moves = (
        possible_non_losing(
            current,
            mask,
        )
    )

    if moves == 0:
        return trunc_div2(
            -(
                BOARD_SIZE
                - moves_played
            )
        )

    # --------------------------------------------------------
    # SCORE BOUNDS
    # --------------------------------------------------------

    minimum = trunc_div2(
        -(
            (
                BOARD_SIZE
                - moves_played
            )
            - 2
        )
    )

    if alpha < minimum:
        if minimum >= beta:
            return minimum

        alpha = minimum

    maximum = (
        (
            BOARD_SIZE
            - moves_played
        )
        - 1
    ) // 2

    if beta > maximum:
        if alpha >= maximum:
            return maximum

        beta = maximum

    # --------------------------------------------------------
    # MOVE ORDERING
    # --------------------------------------------------------

    candidate_moves = np.zeros(
        7,
        dtype=np.uint64,
    )

    candidate_scores = np.full(
        7,
        -1,
        dtype=np.int64,
    )

    candidate_count = 0

    # Match the Rust implementation:
    # iterate centre ordering in reverse
    # while inserting by tactical score.
    for order_index in range(7):
        col = CENTER_ORDER[
            6 - order_index
        ]

        column_mask = (
            np.uint64(
                (1 << ROWS) - 1
            )
            << np.uint64(
                col * BITS_PER_COL
            )
        )

        move = (
            moves
            & column_mask
        )

        if move == 0:
            continue

        score = move_score(
            current,
            mask,
            move,
        )

        insert = candidate_count

        while (
            insert > 0
            and candidate_scores[
                insert - 1
            ] > score
        ):
            candidate_scores[
                insert
            ] = candidate_scores[
                insert - 1
            ]

            candidate_moves[
                insert
            ] = candidate_moves[
                insert - 1
            ]

            insert -= 1

        candidate_scores[
            insert
        ] = score

        candidate_moves[
            insert
        ] = move

        candidate_count += 1

    # Highest tactical score first.
    for candidate_index in range(
        candidate_count - 1,
        -1,
        -1,
    ):
        move = candidate_moves[
            candidate_index
        ]

        child_current = (
            current ^ mask
        )

        child_mask = (
            mask | move
        )

        score = -negamax(
            child_current,
            child_mask,
            moves_played + 1,
            depth - 1,
            -beta,
            -alpha,
            nodes,
            tt_hits,
            keys,
            values,
            flags,
            depths,
            ages,
            age,
        )

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    # --------------------------------------------------------
    # STORE TT RESULT
    # --------------------------------------------------------

    if alpha <= original_alpha:
        flag = TT_UPPER

    elif alpha >= beta:
        flag = TT_LOWER

    else:
        flag = TT_EXACT

    keys[index] = partial_key

    values[index] = np.int8(
        alpha
    )

    flags[index] = flag

    depths[index] = np.uint8(
        depth
    )

    ages[index] = age

    return alpha


# ============================================================
# STRONG SOLVE
# ============================================================

@njit(cache=True)
def solve(
    current,
    mask,
    moves_played,
    nodes,
    tt_hits,
    keys,
    values,
    flags,
    depths,
    ages,
    age,
):
    # Immediate win.
    if can_win_next(
        current,
        mask,
    ):
        return (
            BOARD_SIZE
            + 1
            - moves_played
        ) // 2

    minimum = trunc_div2(
        -(
            BOARD_SIZE
            - moves_played
        )
    )

    maximum = (
        BOARD_SIZE
        + 1
        - moves_played
    ) // 2

    depth = (
        BOARD_SIZE
        - moves_played
    )

    # Binary search exact strong score using
    # repeated null-window Negamax searches.
    while minimum < maximum:
        mid = (
            minimum
            + (
                maximum
                - minimum
            ) // 2
        )

        minimum_half = (
            trunc_div2(
                minimum
            )
        )

        if (
            mid <= 0
            and minimum_half < mid
        ):
            mid = minimum_half

        elif (
            mid >= 0
            and maximum // 2 > mid
        ):
            mid = maximum // 2

        result = negamax(
            current,
            mask,
            moves_played,
            depth,
            mid,
            mid + 1,
            nodes,
            tt_hits,
            keys,
            values,
            flags,
            depths,
            ages,
            age,
        )

        if result <= mid:
            maximum = result

        else:
            minimum = result

    return minimum


# ============================================================
# FIND ONE MOVE MATCHING KNOWN EXACT SCORE
# ============================================================

@njit(cache=True)
def find_move_for_score(
    current,
    mask,
    moves_played,
    target_score,
    nodes,
    tt_hits,
    keys,
    values,
    flags,
    depths,
    ages,
    age,
):
    playable = possible(
        mask
    )

    # Prefer centre-oriented moves.
    for order_index in range(7):
        col = CENTER_ORDER[
            order_index
        ]

        column_mask = (
            np.uint64(
                (1 << ROWS) - 1
            )
            << np.uint64(
                col * BITS_PER_COL
            )
        )

        move = (
            playable
            & column_mask
        )

        if move == 0:
            continue

        # Immediate winning move.
        if (
            winning_positions(
                current,
                mask,
            )
            & move
        ) != 0:
            score = (
                BOARD_SIZE
                - moves_played
                + 1
            ) // 2

        else:
            child_current = (
                current ^ mask
            )

            child_mask = (
                mask | move
            )

            score = -solve(
                child_current,
                child_mask,
                moves_played + 1,
                nodes,
                tt_hits,
                keys,
                values,
                flags,
                depths,
                ages,
                age,
            )

        if score == target_score:
            return col

    return -1


# ============================================================
# PYTHON WRAPPER
# ============================================================

def next_tt_age():
    value = (
        int(TT_AGE[0]) + 1
    ) & 0xFF

    if value == 0:
        # Age 0 is treated as unused.
        # Clear age markers on wraparound.
        TT_AGES.fill(0)

        value = 1

    TT_AGE[0] = value

    return np.uint8(
        value
    )


def find_optimal_move(
    p1,
    p2,
    player,
    target_score,
):
    mask = (
        p1 | p2
    )

    current = (
        p1
        if player == 1
        else p2
    )

    moves_played = (
        mask.bit_count()
    )

    nodes = np.zeros(
        1,
        dtype=np.int64,
    )

    tt_hits = np.zeros(
        1,
        dtype=np.int64,
    )

    age = next_tt_age()

    move = find_move_for_score(
        np.uint64(current),
        np.uint64(mask),
        moves_played,
        int(target_score),
        nodes,
        tt_hits,
        TT_KEYS,
        TT_VALUES,
        TT_FLAGS,
        TT_DEPTHS,
        TT_AGES,
        age,
    )

    return (
        int(move),
        int(nodes[0]),
        int(tt_hits[0]),
    )