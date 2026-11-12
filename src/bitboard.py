# ConnectX bitboard representation
#
# Each column uses 7 bits:
# 6 playable cells + 1 sentinel bit.
#
# Bit index:
#     column * 7 + row_from_bottom

ROWS = 6
COLS = 7
BITS_PER_COL = 7

CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)

BOTTOM_MASK = sum(1 << (c * BITS_PER_COL) for c in range(COLS))

BOARD_MASK = sum(
    ((1 << ROWS) - 1) << (c * BITS_PER_COL)
    for c in range(COLS)
)


def board_to_bitboards(board):
    """
    Convert Kaggle's 42-element board into two bitboards.

    Returns:
        p1: Player 1 pieces
        p2: Player 2 pieces
    """
    p1 = 0
    p2 = 0

    for r in range(ROWS):
        for c in range(COLS):
            value = board[r * COLS + c]

            # Kaggle row 5 = bottom.
            row_from_bottom = ROWS - 1 - r
            bit = 1 << (c * BITS_PER_COL + row_from_bottom)

            if value == 1:
                p1 |= bit
            elif value == 2:
                p2 |= bit

    return p1, p2


def occupied(p1, p2):
    return p1 | p2


def can_play(p1, p2, col):
    """
    True if column still has an empty playable cell.
    """
    occ = occupied(p1, p2)

    top_bit = 1 << (
        col * BITS_PER_COL + ROWS - 1
    )

    return (occ & top_bit) == 0


def valid_moves(p1, p2):
    return [
        c for c in CENTER_ORDER
        if can_play(p1, p2, c)
    ]


def move_bit(p1, p2, col):
    """
    Return the bit corresponding to where a checker
    dropped into col will land.
    """
    occ = occupied(p1, p2)

    column_bottom = 1 << (
        col * BITS_PER_COL
    )

    column_mask = (
        ((1 << ROWS) - 1)
        << (col * BITS_PER_COL)
    )

    return (
        (occ + column_bottom)
        & column_mask
    )


def play_move(p1, p2, col, player):
    """
    Return updated (p1, p2) after player drops
    a checker into col.
    """
    bit = move_bit(p1, p2, col)

    if bit == 0:
        return p1, p2

    if player == 1:
        p1 |= bit
    else:
        p2 |= bit

    return p1, p2


def has_won(position):
    """
    Fast Connect Four detection using bit shifts.
    """

    # Vertical
    m = position & (position >> 1)
    if m & (m >> 2):
        return True

    # Horizontal
    m = position & (position >> 7)
    if m & (m >> 14):
        return True

    # Diagonal /
    m = position & (position >> 6)
    if m & (m >> 12):
        return True

    # Diagonal \
    m = position & (position >> 8)
    if m & (m >> 16):
        return True

    return False


def immediate_wins(p1, p2, player):
    wins = []

    for col in valid_moves(p1, p2):
        n1, n2 = play_move(
            p1,
            p2,
            col,
            player
        )

        position = n1 if player == 1 else n2

        if has_won(position):
            wins.append(col)

    return wins


def winning_positions(position, mask):
    """
    Return a bitmask containing empty squares that would
    complete a Connect Four for 'position'.

    Uses bitboard operations instead of simulating every move.
    """

    result = 0

    # Vertical
    result |= (position << 1) & (position << 2) & (position << 3)

    # Horizontal
    p = (position << 7) & (position << 14)
    result |= p & (position << 21)
    result |= p & (position >> 7)

    p = (position >> 7) & (position >> 14)
    result |= p & (position >> 21)
    result |= p & (position << 7)

    # Diagonal /
    p = (position << 6) & (position << 12)
    result |= p & (position << 18)
    result |= p & (position >> 6)

    p = (position >> 6) & (position >> 12)
    result |= p & (position >> 18)
    result |= p & (position << 6)

    # Diagonal \
    p = (position << 8) & (position << 16)
    result |= p & (position << 24)
    result |= p & (position >> 8)

    p = (position >> 8) & (position >> 16)
    result |= p & (position >> 24)
    result |= p & (position << 8)

    # Only empty playable-board cells
    return result & BOARD_MASK & ~mask


def playable_positions(p1, p2):
    """
    Return a bitmask of every square that can legally
    receive a checker right now.
    """
    mask = p1 | p2

    return (
        (mask + BOTTOM_MASK)
        & BOARD_MASK
    )


def playable_winning_positions(p1, p2, player):
    """
    Winning squares for player that are legally playable
    on the current move.
    """
    position = p1 if player == 1 else p2
    mask = p1 | p2

    wins = winning_positions(
        position,
        mask,
    )

    playable = playable_positions(
        p1,
        p2,
    )

    return wins & playable