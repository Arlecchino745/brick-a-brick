from __future__ import annotations

from . import eliminate
from ._types import Board, PatternCosts, MoveAction
from typing import Optional, List, Tuple


def successors_gen(board: Board, costs: Optional[PatternCosts] = None) -> List[Tuple[Board, float]]:
    """Generate all successor states for the given board and their move costs (legacy compatibility)."""
    return [(result_board, cost) for result_board, cost, _ in successors_with_moves(board, costs)]


def successors_with_moves(board: Board, costs: Optional[PatternCosts] = None) -> List[Tuple[Board, float, MoveAction]]:
    """Generate all successor states for the given board along with move costs and move details."""
    
    if costs is None:
        costs = {}

    successors: List[Tuple[Board, float, MoveAction]] = []
    patterns_pos: List[Tuple[int, int]] = []

    for r in range(len(board)):
        for c in range(len(board)):
            if board[r][c] != 0:
                patterns_pos.append((r, c))

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def _count_labels(b: Board) -> dict[int, int]:
        """Count how many times each label appears on the board."""
        counts: dict[int, int] = {}
        for row in b:
            for v in row:
                if v > 0:
                    counts[v] = counts.get(v, 0) + 1
        return counts
    
    # Capture label counts before performing any move
    before_counts = _count_labels(board)
    
    # Explore reachable empty positions horizontally and vertically from each pattern
    for r_pattern, c_pattern in patterns_pos:
        label = board[r_pattern][c_pattern]
        move_cost = float(costs.get(label, 1.0))

        reachable_empty_pos: List[Tuple[int, int]] = []
        for dr, dc in directions:
            r, c = r_pattern + dr, c_pattern + dc
            while 0 <= r < len(board) and 0 <= c < len(board[0]):
                if board[r][c] == 0:
                    reachable_empty_pos.append((r, c))
                else:
                    break
                r += dr
                c += dc
                
        # Generate a successor state for each reachable empty position
        for r_empty, c_empty in reachable_empty_pos:
            # Perform the move
            temp_board = [row[:] for row in board]
            temp_board[r_pattern][c_pattern] = 0
            temp_board[r_empty][c_empty] = label

            # Apply elimination and capture the resulting board
            successor_board = eliminate.eliminate(temp_board)
            
            # Determine which labels were eliminated
            after_counts = _count_labels(successor_board)
            eliminated_labels = []
            for lab, before_count in before_counts.items():
                if after_counts.get(lab, 0) == 0 and before_count > 0:
                    eliminated_labels.append(lab)
            
            # Create the move action record
            move_action = MoveAction(
                label=label,
                from_pos=(r_pattern, c_pattern),
                to_pos=(r_empty, c_empty),
                cost=move_cost,
                eliminated_labels=sorted(eliminated_labels)
            )
            
            successors.append((successor_board, move_cost, move_action))

    return successors