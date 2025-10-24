import json
import os
import random
from itertools import product

from . import eliminate
from ._types import Board, PatternCosts, PatternsCoords, Coord


def _app_path(*parts: str) -> str:
    
    import sys as _sys
    if getattr(_sys, "frozen", False):
        base = os.path.dirname(_sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _is_pair_valid(
    label: int,
    coords: PatternsCoords,
    size: int,
    existing_pairs: dict[int, PatternsCoords],
    occupied_coords: set[Coord]
) -> bool:
    """Check whether placing a pattern pair in the given coordinates is valid."""
    invalid = (
        label <= 0
        or any(not (0 <= r < size and 0 <= c < size) for r, c in coords)
        or coords[0] == coords[1]
        or label in existing_pairs
        or any(coord in occupied_coords for coord in coords)
    )
    return not invalid


def _create_board_from_pairs(
    size: int,
    pairs: dict[int, PatternsCoords]
) -> Board:
    """Create a board from the provided pattern pairs."""
    board = [[0 for _ in range(size)] for _ in range(size)]
    for label, coords_pair in pairs.items():
        for r, c in coords_pair:
            board[r][c] = label
    return board


def board_load(filename: str) -> tuple[Board, PatternCosts]:
    """Load a board from a JSON file and return its pattern costs."""
    resolved = filename if os.path.isabs(filename) else _app_path(filename)
    with open(resolved, 'r') as file:
        data = json.load(file)
    
    size = data['size']
    pairs: dict[int, PatternsCoords] = {}
    costs: PatternCosts = {}
    occupied: set[tuple[int, int]] = set()
    for pattern in data['patterns']:
        pattern_id = pattern['id']
        positions = pattern['positions']
        cost_val = float(pattern.get('cost', 1.0))
        
        if len(positions) != 2:
            raise ValueError("Invalid data: each pattern must appear in exactly one pair.")
            
        coords = (tuple(positions[0]), tuple(positions[1]))
        
        if not _is_pair_valid(pattern_id, coords, size, pairs, occupied):
            raise ValueError(f"Invalid data for pattern ID {pattern_id}.")
        pairs[pattern_id] = coords
        occupied.update(coords)
        costs[pattern_id] = cost_val
            
    return _create_board_from_pairs(size, pairs), costs


def manual_board_gen() -> tuple[Board, PatternCosts]:
    """Create a board interactively from user input.
    Enter a line as "id cost r1 c1 r2 c2" where:
    - id: positive integer identifying the pattern
    - cost: float or integer specifying the slide cost
    - (r1, c1), (r2, c2): coordinates (0-indexed) for the two tiles
    Submit an empty line to finish and save to data/board_custom.json.
    """
    while True:
        try:
            size = int(input("Enter board size N (e.g., 8 for an 8x8 board, minimum 2): ").strip())
            if size >= 2:
                break
            print("Invalid size: board dimension must be at least 2.")
        except ValueError:
            print("Invalid input: please enter an integer no smaller than 2.")
    
    pairs: dict[int, PatternsCoords] = {}
    occupied: set[tuple[int, int]] = set()
    costs: PatternCosts = {}

    while True:
        entry = input("Enter pattern data (format: 'id cost r1 c1 r2 c2' with coordinates from 0 to N-1) or press Enter to stop: ").strip()

        if not entry:
            print("Input finished; board saved to 'data/board_custom.json'.")
            break

        parts = entry.split()
        if len(parts) != 6:
            print("Invalid data: format is 'id cost r1 c1 r2 c2' (no quotes) with six values; try again.")
            continue
        try:
            label = int(parts[0])
            cost_val = float(parts[1])
            r1, c1, r2, c2 = map(int, parts[2:])
        except ValueError:
            print("Invalid data: id/r1/c1/r2/c2 must be integers and cost numeric; try again.")
            continue

        coords = ((r1, c1), (r2, c2))

        if not _is_pair_valid(label, coords, size, pairs, occupied):
            print("Invalid data: out-of-bounds, duplicate label, or duplicate position detected; try again.")
            continue

        pairs[label] = coords
        occupied.update(coords)
        costs[label] = float(cost_val)

    patterns_data = [{"id": label, "cost": float(costs.get(label, 1.0)), "positions": [list(c) for c in coords]} for label, coords in pairs.items()]
    custom_board_data = {"size": size, "patterns": patterns_data}
    
    out_path = _app_path("data", "board_custom.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as file:
        json.dump(custom_board_data, file, indent=4)

    board = _create_board_from_pairs(size, pairs)
    
    board = eliminate.eliminate(board)
    return board, costs


def random_board_gen(
    size: int | None,
    pair_count: int | None,
    costs: PatternCosts | None = None,
    size_range: tuple[int, int] = (4, 8)
) -> tuple[Board, PatternCosts]:
    """Generate a random board and pattern costs.
    When ``size`` or ``pair_count`` is ``None`` a value is chosen at random within the allowed range.
    - Board size defaults to the range 4..8.
    - If ``costs`` is omitted, each pattern defaults to a cost of ``1.0``.
    - If ``costs`` is provided, it must supply a value for every pattern.
    """

    if size is None:
        min_size, max_size = size_range
        min_size = max(4, min_size)
        max_size = min(8, max_size)
        if min_size > max_size:
            raise ValueError("Invalid size_range: cannot generate a random board size.")
        size = random.randint(min_size, max_size)
    if size < 2:
        raise ValueError("Invalid board size: must be at least 2.")

    max_pairs_allowed = ((size * size) - 1) // 2
    if max_pairs_allowed <= 0:
        raise ValueError("The provided board size cannot accommodate any patterns.")

    if pair_count is None:
        if costs is not None:
            raise ValueError("pair_count must be provided when costs are specified.")
        pair_count = random.randint(1, max_pairs_allowed)

    if pair_count <= 0 or pair_count > max_pairs_allowed:
        raise ValueError("Invalid number of pattern types.")

    validated_costs: PatternCosts | None = None
    if costs is not None:
        validated_costs = {int(k): float(v) for k, v in costs.items()}
        expected_labels = set(range(1, pair_count + 1))
        provided_labels = set(validated_costs.keys())
        missing = expected_labels - provided_labels
        extra = provided_labels - expected_labels
        if missing:
            missing_list = ", ".join(str(label) for label in sorted(missing))
            raise ValueError(f"Missing cost entries for: {missing_list}")
        if extra:
            extra_list = ", ".join(str(label) for label in sorted(extra))
            raise ValueError(f"Unexpected cost entries for: {extra_list}")

    max_attempts = 10000000
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        board = [[0 for _ in range(size)] for _ in range(size)]
        positions = [(i, j) for i, j in product(range(size), repeat=2)]
        random.shuffle(positions)

        for label in range(1, pair_count + 1):
            (r1, c1) = positions.pop()
            (r2, c2) = positions.pop()
            board[r1][c1] = label
            board[r2][c2] = label

        board = eliminate.eliminate(board)
        if sum(1 for row in board for cell in row if cell > 0) == 2 * pair_count:
            if validated_costs is not None:
                return board, dict(validated_costs)
            gen_costs: PatternCosts = {label: 1.0 for label in range(1, pair_count + 1)}
            return board, gen_costs

    raise RuntimeError(f"Timed out: failed to generate a valid board after {max_attempts} attempts.")


def print_board(
    board: Board,
    *,
    cell_width: int | None = None,
    zero_token: str | None = None,
    center: bool = False,
    total_width: int | None = None,
) -> str:
    """Render the board as a formatted string."""
    if not board or not board[0]:
        return ""

    if cell_width is None:
        max_num = max(max(row) for row in board) if board else 0
        cell_width = max(len(str(max_num)), 1)
    if cell_width < 1:
        cell_width = 1

    if zero_token is None:
        zero_token = "." * cell_width

    rows: list[str] = []
    for row in board:
        row_str = ' '.join(
            zero_token if cell == 0 else str(cell).rjust(cell_width)
            for cell in row
        )
        rows.append(row_str)

    if center:
        target_width = total_width if total_width and total_width > 0 else max(len(r) for r in rows)
        rows = [r.center(target_width) for r in rows]

    return '\n'.join(rows)