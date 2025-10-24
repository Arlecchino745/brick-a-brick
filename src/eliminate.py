from __future__ import annotations

from ._types import Board


def eliminate(board: Board) -> Board:
    """
    Remove any pair of matching tiles that can connect horizontally or vertically without obstructions.
    """
    def find_positions() -> dict[int, list[tuple[int, int]]]:
        """
        Collect the current positions of each label on the board.
        """
        positions: dict[int, list[tuple[int, int]]] = {}
        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j] != 0:
                    positions.setdefault(board[i][j], []).append((i, j))
        return positions

    # Repeat elimination until no additional matches are available
    check_need = True
    while check_need:
        check_need = False
        positions = find_positions()

        for pattern_coordinates in positions.values():
            (r1, c1), (r2, c2) = pattern_coordinates
            if r1 == r2:
                if all(board[r1][k] == 0 for k in range(min(c1, c2) + 1, max(c1, c2))):
                    board[r1][c1] = board[r2][c2] =0
                    check_need = True
            elif c1 == c2:
                if all(board[k][c1] == 0 for k in range(min(r1, r2) + 1, max(r1, r2))):
                    board[r1][c1] = board[r2][c2] = 0
                    check_need = True
            
    return board