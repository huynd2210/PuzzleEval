class KubobleGame:
    def __init__(self, level_string, _internal_init_data=None):
        if _internal_init_data:
            self.grid = _internal_init_data['grid']
            self.pieces = _internal_init_data['pieces']
            self.targets = _internal_init_data['targets']
            self.width = _internal_init_data['width']
            self.height = _internal_init_data['height']
        else:
            self.grid = []
            self.pieces = {}  # e.g., {'A': (row, col), 'B': (row, col)}
            self.targets = {} # e.g., {'a': (row, col), 'b': (row, col)}
            self.width = 0
            self.height = 0
            self._parse_level(level_string)

    def _parse_level(self, level_string):
        raw_rows = level_string.strip().split(';')
        self.height = len(raw_rows)
        if self.height == 0:
            self.width = 0
            return

        processed_rows_tokens = [] 
        current_max_width = 0
        for r_idx, row_str_raw in enumerate(raw_rows):
            row_str = row_str_raw.strip()
            current_row_final_tokens = []
            if not row_str:
                pass 
            elif ' ' in row_str: # Space separated takes precedence
                raw_tokens = row_str.split(' ')
                for rt in raw_tokens:
                    if rt: 
                        current_row_final_tokens.append(rt)
            elif '.' in row_str: # Dot implies multiple cells, character separated
                current_row_final_tokens = list(row_str) 
            else: # No spaces, no dots: treat as potentially single cell with multiple occupants or single char piece/target
                  # E.g., "Aa", "A", "ab" (though "ab" is ill-defined by kata for pieces/targets)
                  # For "Aa", this should be one token. For "ABC", it becomes one token "ABC".
                  # The inner loop already handles multi-char tokens like "Aa" correctly if it receives it as one token.
                current_row_final_tokens = [row_str] 
            
            processed_rows_tokens.append(current_row_final_tokens)
            if len(current_row_final_tokens) > current_max_width:
                current_max_width = len(current_row_final_tokens)
        
        self.width = current_max_width

        self.pieces = {}
        self.targets = {}
        
        temp_grid_cell_repr = [['.' for _ in range(self.width)] for _ in range(self.height)]

        for r, token_list_for_row in enumerate(processed_rows_tokens):
            for c, char_cell_content in enumerate(token_list_for_row):
                if c >= self.width: 
                    break 

                temp_grid_cell_repr[r][c] = char_cell_content
                piece_in_cell = None
                target_in_cell = None

                if char_cell_content == 'X': pass
                elif char_cell_content == '.': pass
                else: 
                    if len(char_cell_content) == 1:
                        ch = char_cell_content
                        if 'a' <= ch <= 'z': target_in_cell = ch
                        elif 'A' <= ch <= 'Z': piece_in_cell = ch
                    else: # Multi-character token (e.g., "Aa" from a space-split cell)
                        for sub_char in char_cell_content:
                            if 'a' <= sub_char <= 'z': target_in_cell = sub_char
                            elif 'A' <= sub_char <= 'Z': piece_in_cell = sub_char
                
                if target_in_cell: self.targets[target_in_cell] = (r, c)
                if piece_in_cell: self.pieces[piece_in_cell] = (r, c)

        self.grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        for r_val in range(self.height):
            for c_val in range(self.width):
                # If the token at (r,c) was 'X', mark grid as 'X'
                # This assumes temp_grid_cell_repr was padded if rows were shorter than self.width
                # However, processed_rows_tokens might have short rows. Let's use it directly.
                if r_val < len(processed_rows_tokens) and c_val < len(processed_rows_tokens[r_val]):
                    if processed_rows_tokens[r_val][c_val] == 'X':
                        self.grid[r_val][c_val] = 'X'
                # Otherwise, it remains '.' for now.
        
        for piece_char, (r_pos, c_pos) in self.pieces.items():
            if 0 <= r_pos < self.height and 0 <= c_pos < self.width:
                self.grid[r_pos][c_pos] = piece_char
        
        if 'X' in self.pieces: 
            del self.pieces['X'] # Safeguard

    def is_win(self):
        print(f"DEBUG_IS_WIN_CALLED: Pieces: {self.pieces}, Targets: {self.targets}") # Unconditional print
        if not self.pieces: return False
        for piece_char, target_char in self.get_piece_target_pairs().items():
            if target_char not in self.targets:
                return False 
            if self.pieces[piece_char] != self.targets[target_char]:
                print(f"  IS_WIN_FALSE: {piece_char} at {self.pieces[piece_char]} != {target_char} at {self.targets[target_char]}")
                return False
        print("  IS_WIN_TRUE")
        return True

    def get_piece_target_pairs(self):
        pairs = {}
        for piece_char in self.pieces.keys():
            pairs[piece_char] = piece_char.lower()
        return pairs

    def get_possible_moves(self):
        moves = []
        directions = [(-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right')]

        for piece_char, (r, c) in self.pieces.items():
            for dr, dc, direction_name in directions:
                curr_r, curr_c = r, c
                next_r_start, next_c_start = curr_r + dr, curr_c + dc
                
                if not (0 <= next_r_start < self.height and 0 <= next_c_start < self.width):
                    continue 
                if self.grid[next_r_start][next_c_start] == 'X':
                    continue 
                
                is_blocked_by_piece_at_start = False
                for other_piece, (op_r, op_c) in self.pieces.items():
                    if other_piece != piece_char and (op_r, op_c) == (next_r_start, next_c_start):
                        is_blocked_by_piece_at_start = True
                        break
                if is_blocked_by_piece_at_start:
                    continue

                land_r, land_c = curr_r, curr_c
                while True:
                    next_r, next_c = curr_r + dr, curr_c + dc
                    if not (0 <= next_r < self.height and 0 <= next_c < self.width):
                        land_r, land_c = curr_r, curr_c 
                        break 
                    if self.grid[next_r][next_c] == 'X':
                        land_r, land_c = curr_r, curr_c 
                        break 
                    is_blocked_by_other_piece = False
                    for other_piece, (op_r, op_c) in self.pieces.items():
                        if other_piece != piece_char and (op_r, op_c) == (next_r, next_c):
                            is_blocked_by_other_piece = True
                            break
                    if is_blocked_by_other_piece:
                        land_r, land_c = curr_r, curr_c 
                        break
                    curr_r, curr_c = next_r, next_c
                    land_r, land_c = curr_r, curr_c
                if (land_r, land_c) != (r, c): 
                    moves.append((piece_char, (land_r, land_c), direction_name))
        return moves

    def apply_move(self, piece_char, new_pos, direction_name=None):
        new_grid = [row[:] for row in self.grid]
        new_pieces = self.pieces.copy()
        old_r, old_c = self.pieces[piece_char] 
        new_r, new_c = new_pos
        new_grid[old_r][old_c] = '.'
        new_grid[new_r][new_c] = piece_char
        new_pieces[piece_char] = (new_r, new_c)
        internal_data = {
            'grid': new_grid,
            'pieces': new_pieces,
            'targets': self.targets, 
            'width': self.width,     
            'height': self.height    
        }
        new_game = KubobleGame(level_string=None, _internal_init_data=internal_data)
        return new_game

def verify_kuboble_solution(level_string: str, solution_string: str) -> bool:
    game = KubobleGame(level_string)
    if not solution_string or not solution_string.strip():
        return game.is_win()
    parsed_moves = []
    raw_moves = solution_string.split(';')
    for move_idx, raw_move_unstripped in enumerate(raw_moves):
        raw_move = raw_move_unstripped.strip()
        if not raw_move:
            if move_idx == len(raw_moves) -1 and not parsed_moves: 
                 return game.is_win()
            continue
        parts = raw_move.split()
        if len(parts) != 2:
            return False 
        piece_char, direction_name = parts[0], parts[1].lower()
        if direction_name not in ['up', 'down', 'left', 'right']:
            return False
        parsed_moves.append((piece_char, direction_name))
    if not parsed_moves and solution_string.strip(): 
        return game.is_win()
    current_game_state = game
    for i, (sol_piece_char, sol_direction_name) in enumerate(parsed_moves):
        # Conditional debugging for Test 20
        is_test_20_level = (level_string == "A B . ;X . . ;b a .")

        if is_test_20_level:
            print(f"  [DEBUG_T20] Processing move {i+1}/{len(parsed_moves)}: {sol_piece_char} {sol_direction_name}")
            print(f"    [DEBUG_T20] Current pieces: {current_game_state.pieces}")

        if sol_piece_char not in current_game_state.pieces:
            if is_test_20_level: print(f"    [DEBUG_T20] Piece '{sol_piece_char}' not found. FAILING.")
            return False

        possible_moves_for_current_state = current_game_state.get_possible_moves()
        if is_test_20_level:
            print(f"    [DEBUG_T20] Possible moves from current state: {possible_moves_for_current_state}")
        
        matched_game_move = None
        for pm_piece, pm_new_pos, pm_direction in possible_moves_for_current_state:
            if pm_piece == sol_piece_char and pm_direction == sol_direction_name:
                original_pos = current_game_state.pieces[pm_piece]
                if pm_new_pos != original_pos: 
                    matched_game_move = (pm_piece, pm_new_pos, pm_direction)
                    break
        
        if matched_game_move is None:
            if is_test_20_level: 
                print(f"    [DEBUG_T20] Solution move '{sol_piece_char} {sol_direction_name}' not found in possible_moves. FAILING.")
            return False

        if is_test_20_level:
            print(f"    [DEBUG_T20] Applying matched game move: {matched_game_move}")

        current_game_state = current_game_state.apply_move(matched_game_move[0], matched_game_move[1], matched_game_move[2])
        if is_test_20_level:
            print(f"    [DEBUG_T20] Pieces after apply_move: {current_game_state.pieces}")
            print(f"    [DEBUG_T20] Grid after apply_move (เฉพาะส่วนที่มีชิ้นส่วน):")
            # Print a compact view of the grid relevant to pieces
            min_r = min(p[0] for p in current_game_state.pieces.values()) if current_game_state.pieces else 0
            max_r = max(p[0] for p in current_game_state.pieces.values()) if current_game_state.pieces else current_game_state.height -1
            min_c = min(p[1] for p in current_game_state.pieces.values()) if current_game_state.pieces else 0
            max_c = max(p[1] for p in current_game_state.pieces.values()) if current_game_state.pieces else current_game_state.width -1
            
            temp_display_grid = [['.' for _ in range(current_game_state.width)] for _ in range(current_game_state.height)]
            for r_idx in range(current_game_state.height):
                for c_idx in range(current_game_state.width):
                    if current_game_state.grid[r_idx][c_idx] == 'X':
                        temp_display_grid[r_idx][c_idx] = 'X'
            for p_char, (p_r, p_c) in current_game_state.pieces.items():
                temp_display_grid[p_r][p_c] = p_char
            for t_char, (t_r, t_c) in current_game_state.targets.items():
                if temp_display_grid[t_r][t_c] == '.': # Show target if cell is empty
                    temp_display_grid[t_r][t_c] = t_char
                elif temp_display_grid[t_r][t_c].isupper() and temp_display_grid[t_r][t_c].lower() == t_char: # Piece on its target
                    pass # Piece display takes precedence
                else: # Piece on other target, or target on other target (less likely)
                     pass # Keep piece, or if only target then keep original target mark.

            for r_print in range(current_game_state.height):
                 print(f"      [DEBUG_T20] { ' '.join(temp_display_grid[r_print]) }")


    final_win_state = current_game_state.is_win()
    return final_win_state 

# if __name__ == '__main__':
#     test_cases = [
#         {"level": "Aa", "solution": "", "expected": True, "name": "Already solved"},
#         {"level": "A. ;.a", "solution": "A down; A right", "expected": True, "name": "Simple solvable - Correct (Down, Right)"},
#         {"level": "A. ;.a", "solution": "A right; A down", "expected": True, "name": "Simple solvable - Correct (Right, Down)"},
#         {"level": "A. ;.a", "solution": "A dOwN; A rIgHt", "expected": True, "name": "Simple solvable - Correct (Mixed Case Directions)"},
#         {"level": "A. ;.a", "solution": "A down", "expected": False, "name": "Incorrect solution - Partial, non-win"},
#         {"level": "AX ;.a", "solution": "A right", "expected": False, "name": "Incorrect solution - Blocked by X"},
#         {"level": "AB ;.a", "solution": "A right", "expected": False, "name": "Incorrect solution - Blocked by B"},
#         {"level": "A. ;.a", "solution": "C down", "expected": False, "name": "Invalid input - Piece C not in level"},
#         {"level": "A. ;.a", "solution": "A diagonal", "expected": False, "name": "Invalid input - Invalid direction 'diagonal'"},
#         {"level": "A. ;.a", "solution": "A up down", "expected": False, "name": "Invalid input - Malformed move string"},
#         {"level": "", "solution": "", "expected": False, "name": "Edge case - Empty level, empty solution"},
#         {"level": "a", "solution": "", "expected": False, "name": "Edge case - Target only, empty solution"},
#         {"level": "A", "solution": "", "expected": False, "name": "Edge case - Piece only, empty solution"},
#         {"level": "A. ;.a", "solution": "A down; ; A right;", "expected": True, "name": "Lenient parsing - Extra semicolons and spaces"},
#         {"level": "A. ;.a", "solution": ";;;", "expected": False, "name": "Lenient parsing - Only semicolons, level not solved"},
#         {"level": "Aa", "solution": ";;;", "expected": True, "name": "Lenient parsing - Only semicolons, level IS solved"},
#         {"level": "A.. ; ..a", "solution": "A right", "expected": False, "name": "Sliding - Two-step slide to target"},
#         {"level": "A.X ; ..a", "solution": "A right", "expected": False, "name": "Sliding - Blocked by X mid-slide"},
#         {"level": "A.B;.a.b", "solution": "A down; B down; A right; B right", "expected": True, "name": "Two pieces, simple solution"},
#         {"level": "A B . ;X . . ;b a .", "solution": "B down; A down; B right; A right; B up", "expected": False, "name": "Kata example - 5 moves (corrected order)"},
#         {"level": "A B . ;X . . ;b a .", "solution": "A down; B down; A right; B right; A up", "expected": False, "name": "Kata example - 5 moves (original incorrect order leading to non-win)"},
#         {"level": "A B ;b a", "solution": "A down; B down", "expected": False, "name": "Two pieces, immediate win"},
#         {"level": "A B ;b a", "solution": "B down; A down", "expected": False, "name": "Two pieces, immediate win (alt order)"},
#         {"level": "A B ;b a", "solution": "A down", "expected": False, "name": "Two pieces, partial solution"},
#         # {"level": "X X C B A ;X b . X . ;. . X X c ;X . . a . ", "solution": "C down; B down; A down; C right; B right; A right; C down; B down; A down; C right; B right; A right; C down; B down; A down; B left; A left; B up; A up; A left; C up", "expected": True, "name": "User complex level - Provided solution (21 moves)"},
#     ]
#     passed_count = 0
#     failed_count = 0
#     print("Running Kuboble Solution Verifier Tests:")
#     print("-" * 40)
#     for i, tc in enumerate(test_cases):
#         level = tc["level"]
#         solution = tc["solution"]
#         expected = tc["expected"]
#         name = tc["name"]
#         result = verify_kuboble_solution(level, solution)
#         if result == expected:
#             status = "PASS"
#             passed_count += 1
#         else:
#             status = "FAIL"
#             failed_count += 1
#         print(f"Test {i+1:02d}: [{status}] {name}")
#         if status == "FAIL":
#             print(f"""    Level: '{level}'
#     Solution: '{solution}'
#     Expected: {expected}, Got: {result}""")
#     print("-" * 40)
#     print(f"Summary: {passed_count} passed, {failed_count} failed.")
#     print("-" * 40)

    # Example of how to use it (from a known working test case):
    level_str = "A B . ;X . . ;b a ."
    solution_str = "B down; A down; B right; A right; B up" 
    is_valid = verify_kuboble_solution(level_str, solution_str)
    print(f"Verification for level '{level_str}' with solution '{solution_str}': {is_valid}")

    # level_str_fail = "A.X ; ..a"
    # solution_str_fail = "A right"
    # is_valid_fail = verify_kuboble_solution(level_str_fail, solution_str_fail)
    # print(f"Verification for level '{level_str_fail}' with solution '{solution_str_fail}': {is_valid_fail}") 
