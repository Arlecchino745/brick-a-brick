from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from ._types import Board, PatternCosts, MoveAction, PathNode, PathWithMoves

# Serialized board key type (hashable)
SerializedBoardKey = Tuple[Tuple[int, ...], ...]

Cost = float
GCost = float  # Actual cost from the start node to the current node
FCost = float  # Estimated total cost (g_cost + h_cost)

# Type alias for priority-queue entries
# Stores tuples (f_cost, g_cost, counter, serialized_board_key)
# counter ensures a stable ordering when f_cost and g_cost tie
OpenHeapEntry = Tuple[FCost, GCost, int, SerializedBoardKey]

# Records the path: key is the child, value is (parent, move action)
CameFromMap = Dict[SerializedBoardKey, Tuple[SerializedBoardKey, Optional[MoveAction]]]  
StateCache = Dict[SerializedBoardKey, Board]  # Cache board states to avoid rebuilding board objects
GScoreMap = Dict[SerializedBoardKey, GCost]  # Store g_cost for all known nodes (open and expanded)

# Path type alias represented as a list of board states
Path = List[Board]

from .successor import successors_gen, successors_with_moves


def _serialize(board: Board) -> SerializedBoardKey:
    """
    Convert the board into immutable tuples so it can be used as a dict key or stored in a set.
    """
    return tuple(tuple(row) for row in board)


def _is_goal(board: Board) -> bool:
    """
    Check whether the board has reached the goal state.
    """
    return not any(v for row in board for v in row if v != 0)


def _count_pairs(board: Board) -> int:
    """
    Count how many matching pairs remain on the board.
    """
    counts: Dict[int, int] = {}
    for r in range(len(board)):
        for c in range(len(board[r])):
            v = board[r][c]
            if v > 0:
                counts[v] = counts.get(v, 0) + 1
    return sum(1 for k, v in counts.items() if v == 2)


def _compute_min_cost(costs: Optional[PatternCosts]) -> float:
    """Return the smallest move cost from the cost mapping.

    Falls back to 1.0 if the mapping is missing or invalid.
    """
    if not costs:
        return 1.0
    try:
        return min(float(v) for v in costs.values())
    except (ValueError, TypeError):
        # Fall back to the default value if conversion fails or values are invalid
        return 1.0


def heuristic(
    board: Board,
    costs: Optional[PatternCosts] = None,
    min_cost: Optional[float] = None,
) -> Cost:
    """
    Heuristic (h) = remaining matching pairs * minimum move cost.

    Args:
        board: Current board state.
        costs: Pattern-cost mapping, only used if ``min_cost`` is not provided.
        min_cost: Precomputed minimum move cost; falls back to ``costs`` when ``None``.
    """
    pairs = _count_pairs(board)
    eff_min_cost = _compute_min_cost(costs) if min_cost is None else float(min_cost)
    # pairs equals the number of remaining pattern pairs; each pair requires at least one move
    return float(pairs * eff_min_cost)


def a_star(
    start: Board,
    costs: Optional[PatternCosts] = None,
    max_expansions: Optional[int] = None,
) -> Optional[Tuple[PathWithMoves, Cost]]:
    """
    Run the A* search algorithm to find the minimum-cost path from the start board to the goal.

    Args:
        start: Starting board state.
        costs: Optional mapping of pattern IDs to move costs.
        max_expansions: Optional cap on the number of node expansions.

    Returns:
        A tuple of (path with moves, total cost) if a solution is found; otherwise ``None``.
    """

    if costs is None:
        costs = {}

    if _is_goal(start):
        return [PathNode(start, None)], 0.0

    start_key: SerializedBoardKey = _serialize(start)
    open_heap: List[OpenHeapEntry] = []  # Priority queue of nodes to explore
    counter = 0  # Provides stable ordering when f_cost ties occur

    # g_score stores the best-known cost from the start node to each node
    g_score: GScoreMap = {start_key: 0.0}
    # Pre-compute the global minimum move cost to avoid recomputing in the heuristic
    global_min_cost = _compute_min_cost(costs)
    # Compute the starting node's f_score
    f_start = heuristic(start, costs, global_min_cost)
    # Push the starting node into the priority queue
    heapq.heappush(open_heap, (f_start, 0.0, counter, start_key))

    came_from: CameFromMap = {}  # Track the path
    state_cache: StateCache = {start_key: start}  # Cache board states

    expansions = 0  # Count node expansions

    while open_heap:
        # Pop the node with the lowest f_score from the priority queue
        f_curr, g_curr, _, curr_key = heapq.heappop(open_heap)
        curr_board = state_cache[curr_key]

        # Skip if this node's cost is worse than the recorded best cost
        if g_curr > g_score.get(curr_key, float("inf")):
            continue

        # Goal reached: reconstruct and return the path
        if _is_goal(curr_board):
            path = _reconstruct_path_with_moves(came_from, curr_key, state_cache)
            return path, g_curr

        # Respect the maximum expansion limit if provided
        if max_expansions is not None and expansions >= max_expansions:
            break

        expansions += 1

        # Iterate through each successor (with move information)
        for succ_board, step_cost, move_action in successors_with_moves(curr_board, costs):
            succ_key: SerializedBoardKey = _serialize(succ_board)
            # g_score via the current node
            tentative_g: GCost = g_curr + float(step_cost)
            
            # Best known g_score for this successor
            best_known = g_score.get(succ_key)
            # Skip if the new path is not better
            if best_known is not None and tentative_g >= best_known:
                continue

            # Record the improved path to the successor
            if best_known is None or tentative_g < best_known:
                came_from[succ_key] = (curr_key, move_action)
                g_score[succ_key] = tentative_g
                state_cache[succ_key] = succ_board
                counter += 1
                # Compute successor f_score and push onto the queue
                f_succ: FCost = tentative_g + heuristic(succ_board, costs, global_min_cost)
                heapq.heappush(open_heap, (f_succ, tentative_g, counter, succ_key))

    # No path found if the queue is exhausted
    return None


def _reconstruct_path(
    came_from: Dict[SerializedBoardKey, SerializedBoardKey],
    goal_key: SerializedBoardKey,
    state_cache: StateCache,
) -> Path:
    """Reconstruct a traditional path that only contains board states."""
    path_keys: List[SerializedBoardKey] = [goal_key]
    while path_keys[-1] in came_from:
        path_keys.append(came_from[path_keys[-1]])
    path_keys.reverse()  # Reverse to get start-to-goal order
    return [state_cache[k] for k in path_keys]


def _reconstruct_path_with_moves(
    came_from: CameFromMap,
    goal_key: SerializedBoardKey,
    state_cache: StateCache,
) -> PathWithMoves:
    """Reconstruct a path that also records the moves taken."""
    path_with_moves: List[PathNode] = []
    current_key = goal_key
    
    # Collect path nodes and moves
    path_data: List[Tuple[SerializedBoardKey, Optional[MoveAction]]] = []
    
    while current_key in came_from:
        parent_key, move_action = came_from[current_key]
        path_data.append((current_key, move_action))
        current_key = parent_key
    
    # Add the starting node
    path_data.append((current_key, None))
    
    # Reverse the sequence to build the final path
    path_data.reverse()
    
    for key, move in path_data:
        board = state_cache[key]
        path_with_moves.append(PathNode(board, move))
    
    return path_with_moves


__all__ = [
    "a_star",
    "heuristic",
]
