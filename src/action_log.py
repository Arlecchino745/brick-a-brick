from __future__ import annotations

from typing import List, Tuple, cast

from ._types import Board, PathWithMoves
from .board_gen import print_board


def generate_action_log(path_with_moves: PathWithMoves, show_boards: bool = True) -> str:
    """Efficiently generate a readable log for a sequence of moves."""
    if not path_with_moves:
        return ""

    entries: List[Tuple[str, str | Board]] = []
    text_width = 0
    all_boards = []

    def add_text(line: str) -> None:
        nonlocal text_width
        entries.append(("text", line))
        text_width = max(text_width, len(line))

    def add_blank() -> None:
        add_text("")

    def add_board(board) -> None:
        entries.append(("board", board))
        all_boards.append(board)

    add_text("== Initial Board ==")
    add_board(path_with_moves[0].board)
    add_blank()

    total_cost = 0.0

    for i in range(1, len(path_with_moves)):
        node = path_with_moves[i]
        move = node.move
        
        if move is None:
            add_text(f"STEP{i}: [No move information]")
            if show_boards:
                add_board(node.board)
                add_blank()
            continue
            
        total_cost += move.cost
        add_text(
            f"STEP{i}: move label {move.label} from {move.from_pos} to {move.to_pos} | cost={move.cost:.3f}"
        )
        
        if move.eliminated_labels:
            add_text(f"         patterns {move.eliminated_labels} eliminated")
        
        if show_boards:
            add_board(node.board)
            add_blank()

    add_text(f"== Steps completed: {max(0, len(path_with_moves)-1)} total cost: {total_cost:.3f} ==")

    max_cell_value = 0
    for board in all_boards:
        if not board or not board[0]:
            continue
        board_max = max(max(row) for row in board)
        max_cell_value = max(max_cell_value, board_max)

    cell_width = max(len(str(max_cell_value)), 1)

    board_line_lengths = []
    for board in all_boards:
        if not board or not board[0]:
            continue
        columns = len(board[0])
        board_line_lengths.append(columns * cell_width + max(0, columns - 1))

    target_width = max(text_width, max(board_line_lengths, default=0))

    lines: List[str] = []
    for kind, payload in entries:
        if kind == "text":
            lines.append(cast(str, payload))
        elif kind == "board":
            board_payload = cast(Board, payload)
            lines.append(
                print_board(
                    board_payload,
                    cell_width=cell_width,
                    center=True,
                    total_width=target_width,
                )
            )

    return "\n".join(lines)


def output_action_log(path_with_moves: PathWithMoves, show_boards: bool = True) -> None:
    """Print the move sequence log."""
    print(generate_action_log(path_with_moves, show_boards))


__all__ = [
    "generate_action_log",
    "output_action_log",
]