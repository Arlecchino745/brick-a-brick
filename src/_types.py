from __future__ import annotations
from typing import TypeAlias, NamedTuple, Optional, List

Board: TypeAlias = list[list[int]]
Coord: TypeAlias = tuple[int, int]
PatternsCoords: TypeAlias = tuple[Coord, Coord]
Successors: TypeAlias = list[Board]
PatternCosts: TypeAlias = dict[int, float]

# Detailed information about a move action
class MoveAction(NamedTuple):
    """Capture the full details of a single move."""
    label: int  # Label being moved
    from_pos: Coord  # Starting position
    to_pos: Coord  # Target position
    cost: float  # Move cost
    eliminated_labels: List[int]  # Labels removed after elimination

# Extended path node that tracks move information
class PathNode(NamedTuple):
    """Path node containing the board state and the move that reached it."""
    board: Board
    move: Optional[MoveAction]  # None indicates the start state

# Complete path type
PathWithMoves: TypeAlias = List[PathNode]