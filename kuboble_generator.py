import random
from collections import deque

# Assuming kuboble_verifier.py is in the same directory or accessible in PYTHONPATH
# If not, you might need to adjust the import path or ensure it's installed as a module.
try:
    from .kuboble_verifier import KubobleGame
except ImportError:
    # Fallback if run as a script and kuboble_verifier is in the same directory
    from kuboble_verifier import KubobleGame

def _coords_to_level_string(width, height, pieces_pos, targets_pos, obstacles_pos):
    """
    Converts dictionaries of piece, target, and obstacle positions to a Kuboble level string.
    """
    grid = [['.' for _ in range(width)] for _ in range(height)]

    for r, c in obstacles_pos:
        if 0 <= r < height and 0 <= c < width:
            grid[r][c] = 'X'

    for piece_char, (r, c) in pieces_pos.items():
        if 0 <= r < height and 0 <= c < width:
            # If target is at the same spot, represent as "Aa"
            target_char = piece_char.lower()
            if targets_pos.get(target_char) == (r, c):
                grid[r][c] = piece_char + target_char
                # Remove target from targets_pos to avoid double printing
                del targets_pos[target_char]
            else:
                grid[r][c] = piece_char

    for target_char, (r, c) in targets_pos.items():
        if 0 <= r < height and 0 <= c < width:
            if grid[r][c] == '.': # Only place if cell is empty
                grid[r][c] = target_char
            # If a piece is already there but it's NOT its corresponding piece, this is complex.
            # For simplicity, this generator prioritizes piece_char+target_char if they coincide.
            # Otherwise, piece char takes precedence if placed first.

    return ";".join(" ".join(row) for row in grid)


def _is_solvable_bfs(game_instance: KubobleGame, max_depth=20):
    """
    Checks if a Kuboble game instance is solvable using BFS.
    Returns the solution string if solvable within max_depth, None otherwise.
    """
    if game_instance.is_win():
        return "" # Already solved, no moves needed

    # queue stores (game_state, current_path_string, depth)
    queue = deque([(game_instance, [], 0)]) 
    visited_states = set()

    initial_pieces_tuple = tuple(sorted(game_instance.pieces.items()))
    visited_states.add(initial_pieces_tuple)

    while queue:
        current_game, current_path, depth = queue.popleft()

        if depth >= max_depth:
            continue

        possible_moves = current_game.get_possible_moves()
        for piece_char, new_pos, direction_name in possible_moves:
            next_game_state = current_game.apply_move(piece_char, new_pos, direction_name)
            move_str = f"{piece_char} {direction_name}"
            new_path = current_path + [move_str]
            
            if next_game_state.is_win():
                return ";".join(new_path)

            pieces_tuple = tuple(sorted(next_game_state.pieces.items()))
            
            if pieces_tuple not in visited_states:
                visited_states.add(pieces_tuple)
                queue.append((next_game_state, new_path, depth + 1))
    return None # Not solvable within max_depth

def generate_kuboble_level(
    width: int,
    height: int,
    num_pieces: int,
    num_obstacles: int,
    max_generation_attempts: int = 100,
    max_solver_depth: int = 25, # Max moves to consider for solvability
    require_non_trivial_solution: bool = True
) -> tuple[str, str] | None: # Returns (level_string, solution_string) or None
    """
    Generates a solvable Kuboble level string and its solution.

    Args:
        width: The width of the grid.
        height: The height of the grid.
        num_pieces: The number of pieces (A, B, C, ...).
        num_obstacles: The number of obstacles (X).
        max_generation_attempts: Max attempts to find a solvable level.
        max_solver_depth: Max depth for the BFS solver to check solvability.
        require_non_trivial_solution: If True, ensures the generated puzzle isn't already solved.

    Returns:
        A tuple (level_string, solution_string) if a solvable puzzle is found, otherwise None.
    """
    if num_pieces == 0:
        # For a game with no pieces, it's trivially solved with an empty solution.
        return _coords_to_level_string(width, height, {}, {}, []), ""

    if num_pieces > 26:
        raise ValueError("Number of pieces cannot exceed 26 (A-Z).")
    
    total_cells = width * height
    if num_pieces * 2 + num_obstacles > total_cells:
        raise ValueError("Not enough cells for the requested pieces, targets, and obstacles.")

    for attempt in range(max_generation_attempts):
        all_coords = [(r, c) for r in range(height) for c in range(width)]
        random.shuffle(all_coords)

        pieces_pos = {}
        targets_pos = {}
        obstacles_pos = []

        # Place pieces and their targets
        current_piece_char_code = ord('A')
        placed_items_count = 0
        
        temp_occupied_coords = set()

        for i in range(num_pieces):
            if len(all_coords) < 2: # Need 2 cells for piece and target
                break 
            
            piece_coord = all_coords.pop()
            target_coord = all_coords.pop()
            
            piece_char = chr(current_piece_char_code + i)
            target_char = piece_char.lower()
            
            pieces_pos[piece_char] = piece_coord
            targets_pos[target_char] = target_coord
            
            temp_occupied_coords.add(piece_coord)
            temp_occupied_coords.add(target_coord)
            placed_items_count += 2
        
        if len(pieces_pos) != num_pieces: # Could not place all pieces and targets
            continue 

        # Place obstacles
        for _ in range(num_obstacles):
            if not all_coords:
                break
            obstacle_coord = all_coords.pop()
            obstacles_pos.append(obstacle_coord)
            temp_occupied_coords.add(obstacle_coord)
            placed_items_count += 1

        level_string = _coords_to_level_string(width, height, pieces_pos.copy(), targets_pos.copy(), obstacles_pos[:])
        
        try:
            game = KubobleGame(level_string)
        except Exception as e:
            continue # Parsing error or invalid setup

        # Check for non-trivial solution if required
        # An already solved game has an empty string solution from _is_solvable_bfs
        current_solution = _is_solvable_bfs(game, 0) # Check if initially solved
        if require_non_trivial_solution and current_solution == "":
            continue

        # Now, find a full solution if not initially solved, or confirm solvability
        solution = _is_solvable_bfs(game, max_solver_depth)
        if solution is not None:
            return level_string, solution

    return None

def _verify_generated_solution(level_str: str, solution_str: str, game_class_for_verifier) -> bool:
    """Helper function to verify if the generated solution solves the level."""
    if solution_str is None: # Should not happen if generate_kuboble_level returned a level
        print("  Verification Error: No solution string provided for a generated level.")
        return False

    verifier_game = game_class_for_verifier(level_str)
    temp_game = verifier_game
    verified_correctly = False

    if not solution_str:  # Empty solution means it should already be a win
        verified_correctly = temp_game.is_win()
        if not verified_correctly:
            print("  Verification Error: Empty solution provided, but game is not initially won.")
    else:
        moves = solution_str.split(';')
        possible_to_apply_all = True
        for i, move_raw in enumerate(moves):
            parts = move_raw.strip().split()
            if len(parts) != 2:
                print(f"  Verification Error: Malformed move '{move_raw}' in generated solution.")
                possible_to_apply_all = False; break
            
            m_piece, m_dir = parts[0], parts[1].lower() # Ensure direction is lower for matching

            actual_move_for_verifier = None
            current_possible_moves = temp_game.get_possible_moves()
            for p_m_p, p_m_new_pos, p_m_dir in current_possible_moves:
                if p_m_p == m_piece and p_m_dir == m_dir:
                    actual_move_for_verifier = (p_m_p, p_m_new_pos, p_m_dir)
                    break
            
            if actual_move_for_verifier:
                temp_game = temp_game.apply_move(actual_move_for_verifier[0], actual_move_for_verifier[1], actual_move_for_verifier[2])
            else:
                print(f"  Verification Error: Generated solution move {i+1} ('{move_raw}') not possible from current state.")
                print(f"    Available moves: {current_possible_moves}")
                print(f"    Current pieces: {temp_game.pieces}")
                possible_to_apply_all = False; break
        
        if possible_to_apply_all:
            verified_correctly = temp_game.is_win()
            if not verified_correctly:
                 print("  Verification Error: All solution moves applied, but game is not won.")

    print(f"Solution verified by applying moves: {verified_correctly}")
    return verified_correctly

def _run_generation_example(w, h, p, o, depth, game_class):
    """Runs a single generation example, prints level, solution, and verifies."""
    print(f"\nAttempting to generate: {w}x{h}, {p} pieces, {o} obstacles, solver depth {depth}")
    generated_data = generate_kuboble_level(width=w, height=h, num_pieces=p, num_obstacles=o, max_solver_depth=depth)
    
    if generated_data:
        level_str, solution_str = generated_data
        num_moves = len(solution_str.split(';')) if solution_str else 0
        print(f"Generated Level ({num_moves} moves):\n{level_str.replace(';', '\n')}")
        print(f"Solution:\n{solution_str}")
        _verify_generated_solution(level_str, solution_str, game_class)
    else:
        print("Failed to generate a solvable level with the given parameters.")

if __name__ == '__main__':
    print("Generating Kuboble Levels...")

    _run_generation_example(w=5, h=5, p=3, o=5, depth=20, game_class=KubobleGame)

