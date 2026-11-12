import time

# ============================================================
# V4 - ITERATIVE DEEPENING + ALPHA-BETA
# ============================================================

V4_ORDER = (3, 2, 4, 1, 5, 0, 6)

V4_START = 0
V4_LIMIT = 1.65
V4_TT = {}

WIN_SCORE = 1_000_000


class V4Timeout(Exception):
    pass


def v4_check_time():
    if time.perf_counter() - V4_START >= V4_LIMIT:
        raise V4Timeout


def v4_valid(board):
    return [c for c in V4_ORDER if board[c] == 0]


def v4_drop(board, col, piece):
    b = list(board)

    for r in range(5, -1, -1):
        i = r * 7 + col

        if b[i] == 0:
            b[i] = piece
            return tuple(b)

    return board


def v4_win(board, piece):

    # Horizontal
    for r in range(6):
        base = r * 7

        for c in range(4):
            i = base + c

            if (
                board[i] == piece and
                board[i + 1] == piece and
                board[i + 2] == piece and
                board[i + 3] == piece
            ):
                return True

    # Vertical
    for r in range(3):
        for c in range(7):
            i = r * 7 + c

            if (
                board[i] == piece and
                board[i + 7] == piece and
                board[i + 14] == piece and
                board[i + 21] == piece
            ):
                return True

    # Down-right diagonal
    for r in range(3):
        for c in range(4):
            i = r * 7 + c

            if (
                board[i] == piece and
                board[i + 8] == piece and
                board[i + 16] == piece and
                board[i + 24] == piece
            ):
                return True

    # Up-right diagonal
    for r in range(3, 6):
        for c in range(4):
            i = r * 7 + c

            if (
                board[i] == piece and
                board[i - 6] == piece and
                board[i - 12] == piece and
                board[i - 18] == piece
            ):
                return True

    return False


def v4_immediate_wins(board, piece):
    wins = []

    for col in v4_valid(board):
        child = v4_drop(board, col, piece)

        if v4_win(child, piece):
            wins.append(col)

    return wins


def v4_window_score(a, b, c, d, piece):
    opponent = 3 - piece

    own = (
        (a == piece) +
        (b == piece) +
        (c == piece) +
        (d == piece)
    )

    enemy = (
        (a == opponent) +
        (b == opponent) +
        (c == opponent) +
        (d == opponent)
    )

    empty = 4 - own - enemy

    if own and enemy:
        return 0

    if own == 4:
        return 100000

    if enemy == 4:
        return -100000

    if own == 3 and empty == 1:
        return 120

    if enemy == 3 and empty == 1:
        return -150

    if own == 2 and empty == 2:
        return 15

    if enemy == 2 and empty == 2:
        return -18

    if own == 1 and empty == 3:
        return 2

    if enemy == 1 and empty == 3:
        return -2

    return 0


def v4_evaluate(board, piece):
    score = 0
    opponent = 3 - piece

    # Center control
    for r in range(6):
        value = board[r * 7 + 3]

        if value == piece:
            score += 10
        elif value == opponent:
            score -= 10

    # Horizontal
    for r in range(6):
        base = r * 7

        for c in range(4):
            i = base + c

            score += v4_window_score(
                board[i],
                board[i + 1],
                board[i + 2],
                board[i + 3],
                piece
            )

    # Vertical
    for r in range(3):
        for c in range(7):
            i = r * 7 + c

            score += v4_window_score(
                board[i],
                board[i + 7],
                board[i + 14],
                board[i + 21],
                piece
            )

    # Down-right diagonal
    for r in range(3):
        for c in range(4):
            i = r * 7 + c

            score += v4_window_score(
                board[i],
                board[i + 8],
                board[i + 16],
                board[i + 24],
                piece
            )

    # Up-right diagonal
    for r in range(3, 6):
        for c in range(4):
            i = r * 7 + c

            score += v4_window_score(
                board[i],
                board[i - 6],
                board[i - 12],
                board[i - 18],
                piece
            )

    return score


def v4_order_moves(board, moves, turn):
    scored = []

    for col in moves:

        # Center preference
        priority = 10 - abs(3 - col)

        child = v4_drop(board, col, turn)

        # Search winning moves first
        if v4_win(child, turn):
            priority += 10000

        scored.append((priority, col))

    scored.sort(reverse=True)

    return [col for _, col in scored]


def v4_search(
    board,
    depth,
    alpha,
    beta,
    turn,
    root_piece,
    ply
):
    v4_check_time()

    opponent = 3 - root_piece

    if v4_win(board, root_piece):
        return WIN_SCORE - ply

    if v4_win(board, opponent):
        return -WIN_SCORE + ply

    moves = v4_valid(board)

    if not moves:
        return 0

    if depth == 0:
        return v4_evaluate(board, root_piece)

    key = (
        board,
        depth,
        turn,
        root_piece
    )

    cached = V4_TT.get(key)

    if cached is not None:
        return cached

    moves = v4_order_moves(
        board,
        moves,
        turn
    )

    if turn == root_piece:

        value = -10**9

        for col in moves:
            child = v4_drop(
                board,
                col,
                turn
            )

            value = max(
                value,
                v4_search(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    3 - turn,
                    root_piece,
                    ply + 1
                )
            )

            alpha = max(alpha, value)

            if alpha >= beta:
                break

    else:

        value = 10**9

        for col in moves:
            child = v4_drop(
                board,
                col,
                turn
            )

            value = min(
                value,
                v4_search(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    3 - turn,
                    root_piece,
                    ply + 1
                )
            )

            beta = min(beta, value)

            if alpha >= beta:
                break

    V4_TT[key] = value

    return value


def v4_root(board, piece, depth):
    moves = v4_valid(board)

    moves = v4_order_moves(
        board,
        moves,
        piece
    )

    best_move = moves[0]
    best_score = -10**9

    alpha = -10**9
    beta = 10**9

    for col in moves:

        v4_check_time()

        child = v4_drop(
            board,
            col,
            piece
        )

        score = v4_search(
            child,
            depth - 1,
            alpha,
            beta,
            3 - piece,
            piece,
            1
        )

        if score > best_score:
            best_score = score
            best_move = col

        alpha = max(alpha, best_score)

    return best_move, best_score


# ============================================================
# KAGGLE ENTRY POINT
# ============================================================

def agent(observation, configuration):
    global V4_START
    global V4_TT

    V4_START = time.perf_counter()
    V4_TT = {}

    board = tuple(observation.board)

    piece = observation.mark
    opponent = 3 - piece

    moves = v4_valid(board)

    if not moves:
        return 0

    # Win immediately
    wins = v4_immediate_wins(
        board,
        piece
    )

    if wins:
        return int(wins[0])

    # Block immediate opponent win
    opponent_wins = v4_immediate_wins(
        board,
        opponent
    )

    if opponent_wins:
        return int(opponent_wins[0])

    # Safe fallback
    best_move = moves[0]

    # Iterative deepening
    depth = 1

    try:

        while depth <= 12:

            move, score = v4_root(
                board,
                piece,
                depth
            )

            # Save only fully completed depths
            best_move = move

            # Forced win found
            if score >= WIN_SCORE - 50:
                break

            depth += 1

    except V4Timeout:
        pass

    return int(best_move)