from __future__ import annotations

import itertools
import os
import sys
import threading
from contextlib import contextmanager
from typing import Optional, Tuple

from src._types import Board, PatternCosts
from src.board_gen import board_load, manual_board_gen, random_board_gen, print_board
from src.a_star import a_star
from src.action_log import output_action_log


def _app_path(*parts: str) -> str:

	import sys as _sys
	if getattr(_sys, "frozen", False):
		base = os.path.dirname(_sys.executable)
	else:
		base = os.path.dirname(os.path.abspath(__file__))
	return os.path.join(base, *parts)


def _load_board_from_file(path: str) -> Tuple[Board, PatternCosts]:
	resolved = path if os.path.isabs(path) else _app_path(path)
	if not os.path.exists(resolved):
		raise FileNotFoundError(f"File not found: {resolved}")
	return board_load(resolved)


@contextmanager
def _search_spinner(message: str = "Searching"):
	"""Display a transient spinner while the search runs."""
	stop_event = threading.Event()
	display_width = len(message) + 3  # reserve space for up to three dots
	dot_cycle = itertools.cycle(range(4))

	def _spin() -> None:
		while not stop_event.is_set():
			dot_count = next(dot_cycle)
			dots = "." * dot_count
			padding = max(display_width - len(message) - len(dots), 0)
			sys.stdout.write(f"\r{message}{dots}" + (" " * padding))
			sys.stdout.flush()
			if stop_event.wait(0.3):
				break

	spinner_thread = threading.Thread(target=_spin, daemon=True)
	spinner_thread.start()
	try:
		yield
	finally:
		stop_event.set()
		spinner_thread.join()
		sys.stdout.write("\r" + (" " * display_width) + "\r")
		sys.stdout.flush()


def run_interactive() -> int:
	print("\n[Brick-a-brick] Solve the Brick-a-brick puzzle with A*; choose a mode:\n")
	print("    1) Load from example or custom JSON file")
	print("    2) Build a custom board (saved to data/board_custom.json)")
	print("    3) Pick board size and pattern count to generate randomly")
	
	choice = ""
	while choice not in ("1", "2", "3"):
		choice = input("\nEnter 1/2/3 (press Enter for the default of 3): ").strip() or "3"
		if choice not in ("1", "2", "3"):
			print("Invalid option; please try again.")

	board: Board = []
	costs: PatternCosts = {}
	show_costs = False

	try:
		if choice == "1":
			custom_path = os.path.join("data", "board_custom.json")
			example_path = os.path.join("data", "board_example.json")
			
			has_custom = os.path.exists(custom_path)
			
			if has_custom:
				print("\nSelect the board to load:")
				print("    1) Example board (same as the assignment, board_example.json)")
				print("    2) Custom board (board_custom.json)")
				
				board_choice = ""
				while board_choice not in ("1", "2"):
					board_choice = input("Enter 1/2 (press Enter for the default of 1): ").strip() or "1"
					if board_choice not in ("1", "2"):
						print("Invalid option; please try again.")
				
				path = example_path if board_choice == "1" else custom_path
			else:
				print(f"\nNote: custom board file not found ({_app_path(custom_path)})")
				print(f"Loading the example board instead ({_app_path(example_path)})")
				path = example_path
			
			board, costs = _load_board_from_file(path)
		elif choice == "2":
			board, costs = manual_board_gen()
		elif choice == "3":
			print("\nRandom board configuration options:")
			print("    1) Manually set board size and number of pattern types")
			print("    2) Randomize board size and pattern types (size range 4-8)")
			mode_choice = ""
			while mode_choice not in ("1", "2"):
				mode_choice = input("Enter 1/2 (press Enter for the default of 2): ").strip() or "2"
				if mode_choice not in ("1", "2"):
					print("Invalid option; please try again.")

			size: Optional[int]
			pairs: Optional[int]
			if mode_choice == "1":
				while True:
					try:
						size_s = input("Enter board size (e.g., 8 for an 8x8 board, minimum 2): ").strip()
						size = int(size_s)
						if size < 2:
							print("Board size must be at least 2.")
							continue
						break
					except ValueError:
						print("Invalid input; enter an integer.")
				max_pairs_allowed = ((size * size) - 1) // 2
				while True:
					try:
						pairs_s = input("Enter the number of pattern types: ").strip()
						pairs = int(pairs_s)
						if pairs <= 0:
							print("Pattern count must be greater than 0.")
							continue
						if pairs > max_pairs_allowed:
							print(f"Pattern count must be <= {max_pairs_allowed} to leave empty spaces.")
							continue
						break
					except ValueError:
						print("Invalid input; enter an integer.")
			else:
				size = None
				pairs = None

			board, costs = random_board_gen(size, pairs)
			pattern_labels = sorted(costs.keys())
			if board:
				side_len = len(board)
				col_len = len(board[0]) if board[0] else 0
				pattern_types = len(pattern_labels)
				label_preview = ", ".join(str(label) for label in pattern_labels) if pattern_labels else "none"
				print(f"\nRandom board dimensions: {side_len} x {col_len}")
				print(f"Pattern types: {pattern_types}" + (f" (labels: {label_preview})" if pattern_labels else ""))
			if pattern_labels:
				while True:
					custom_cost_input = input("Assign a cost for each pattern? (y/N): ").strip().lower()
					if custom_cost_input in ('y', 'n', ''):
						break
					print("Invalid input; enter 'y' or 'n'.")
				if custom_cost_input == 'y':
					show_costs = True
					new_costs: PatternCosts = {}
					for label in pattern_labels:
						while True:
							cost_str = input(f"Enter the cost for pattern {label} (press Enter for 1): ").strip()
							if cost_str == "":
								new_costs[label] = 1.0
								break
							try:
								new_costs[label] = float(cost_str)
								break
							except ValueError:
								print("Invalid input; enter a numeric value.")
					costs = new_costs
	except Exception as e:
		print(f"Error while preparing the board: {e}")
		return 2

	print("\nInitial board:")
	info_width = len("Initial board:")
	cell_width_override: Optional[int] = None
	board_line_width = 0
	if board:
		side_len = len(board)
		pattern_types = len({cell for row in board for cell in row if cell > 0})
		info_line = f"Board dimensions: {side_len} x {len(board[0])}, pattern types: {pattern_types}"
		print(info_line)
		info_width = max(info_width, len(info_line))
		columns = len(board[0]) if board and board[0] else 0
		if columns:
			max_val = max((cell for row in board for cell in row), default=0)
			cell_width_override = max(len(str(max_val)), 1)
			board_line_width = columns * cell_width_override + max(0, columns - 1)
	board_total_width = max(info_width, board_line_width)
	print(
		print_board(
			board,
			cell_width=cell_width_override,
			center=True,
			total_width=board_total_width,
		)
	)
	if show_costs:
		print("\nPattern costs:")
		for label in sorted(costs):
			print(f"    Pattern {label}: {costs[label]:.3f}")

	max_expansions: Optional[int] = None
	while True:
		limit_exp = input("Set a maximum number of expanded nodes (enter a number or leave blank for no limit): ").strip()
		if not limit_exp:
			break
		try:
			max_expansions = int(limit_exp)
			break
		except ValueError:
			print("Invalid input; enter an integer.")

	with _search_spinner("Searching"):
		result = a_star(board, costs, max_expansions=max_expansions)
	if result is None:
		print("No solution found.")
		return 1

	path, total_cost = result
	output_action_log(path, show_boards=True)
	print(f"Total steps: {len(path)-1}, total cost: {total_cost:.3f}")
	return 0


def _should_pause(argv: list[str]) -> bool:

	if "--pause" in argv:
		return True
	if "--no-pause" in argv:
		return False
	if getattr(sys, "frozen", False):

		val = os.environ.get("BRICK_NO_PAUSE")
		if val is None:
			return True
		val = val.strip().lower()
		return not (val in ("1", "true", "yes", "on", "y", "t"))
	return False


def main(argv: Optional[list[str]] = None) -> int:
	if argv is None:
		argv = sys.argv[1:]

	pause_flag = _should_pause(argv)
	argv[:] = [a for a in argv if a not in ("--pause", "--no-pause")]

	code = run_interactive()

	if pause_flag:
		try:
			input("\nSearch complete. Press Enter to exit.")
		except EOFError:

			pass
	return code


if __name__ == "__main__":
	sys.exit(main())