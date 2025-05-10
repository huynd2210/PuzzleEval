import random
import itertools
from collections import Counter
import yaml
import argparse

def all_codes(colors=6, pegs=4):
    """Return a list of all possible codes as tuples of integers 0..colors-1."""
    return list(itertools.product(range(colors), repeat=pegs))

def score_feedback(secret, guess):
    """
    Return (black, white) feedback for a single guess against the secret.
    black = correct color & position
    white = correct color wrong position
    """
    # Count blacks
    blacks = sum(s == g for s, g in zip(secret, guess))
    # Count whites
    # For whites, count color matches minus blacks
    secret_counts = Counter(secret)
    guess_counts  = Counter(guess)
    common_colors = sum((secret_counts & guess_counts).values())
    whites = common_colors - blacks
    return blacks, whites

def is_unique_solution(clues, all_codes_list, debug=False):
    """
    Given clues = list of (guess, feedback) pairs,
    return True if exactly one code in all_codes_list fits them all.
    """
    if debug: print(f"DEBUG is_unique_solution: Checking {len(clues)} clues: {clues}")
    candidates = []
    for code in all_codes_list:
        match = True
        for guess, fb in clues:
            if score_feedback(code, guess) != fb:
                match = False
                break
        if match:
            candidates.append(code)
            # Optimization: if we find more than one early, we might stop early depending on context
            # For strict uniqueness check, we need to check all codes unless we only care *if* it's unique
            # if len(candidates) > 1: 
            #     # return False # Returning early might be wrong if we need the full candidate list later
            #     pass

    is_unique = len(candidates) == 1
    if debug: print(f"DEBUG is_unique_solution: Found {len(candidates)} candidates: {candidates}. Is unique? {is_unique}")
    # Return both the boolean and the list of candidates for detailed checking
    return is_unique, candidates 

def find_solution_clues(secret, all_codes_list, max_guesses=10):
    """
    Build a list of (guess, feedback) until uniqueness is reached.
    Guesses are chosen randomly from all_codes_list.
    """
    clues = []
    # Use a copy to avoid modifying the original list if passed from outside
    potential_guesses = all_codes_list[:] 
    random.shuffle(potential_guesses)
    
    # Ensure the secret code itself isn't accidentally used as the first guess
    # (while not strictly necessary, it makes for slightly better puzzles)
    if secret in potential_guesses:
        potential_guesses.remove(secret)

    # Add guesses one by one until the solution is unique
    for guess in potential_guesses:
        if len(clues) >= max_guesses:
            # Stop if we exceed the maximum allowed guesses
            break 
            
        fb = score_feedback(secret, guess)
        # Avoid adding trivial clues (like 0 black, 0 white if not necessary)
        # or duplicate clues (same guess, same feedback - though unlikely with random)
        if (guess, fb) not in clues: 
             clues.append((guess, fb))
             # Check for uniqueness only after adding a new clue
             # Pass debug=True for verbose output during initial clue finding if needed
             is_unique, _ = is_unique_solution(clues, all_codes_list, debug=False) 
             if is_unique:
                 return clues

    # If loop finishes without finding a unique solution
    raise ValueError(f"Failed to isolate the secret {secret} within {max_guesses} guesses. The current clues identify {len([c for c in all_codes_list if all(score_feedback(c, g) == fb for g, fb in clues)])} candidates.")

def prune_redundant(clues, all_codes_list, secret_code, debug=False):
    """
    Remove any guess in clues that is redundant.
    A clue is redundant if clues minus it still has a unique solution
    (which must be the original secret_code).
    """
    if debug: print(f"DEBUG prune_redundant: Starting pruning with {len(clues)} clues for secret {secret_code}.")
    pruned_clues = clues[:] # Work on a copy
    i = 0
    while i < len(pruned_clues):
        clue_to_test = pruned_clues[i]
        if debug: print(f"\nDEBUG prune_redundant: Testing removal of clue #{i+1} ({clue_to_test}) from current {len(pruned_clues)} clues.")
        
        # Create a temporary list without the clue at index i
        temp_clues = pruned_clues[:i] + pruned_clues[i+1:]
        
        # Need at least one clue left to be solvable
        if not temp_clues:
             if debug: print("DEBUG prune_redundant: Cannot remove, would leave 0 clues.")
             i += 1
             continue

        if debug: print(f"DEBUG prune_redundant: Checking uniqueness with remaining {len(temp_clues)} clues: {temp_clues}")
        # Check if the reduced set of clues still uniquely identifies the secret
        is_still_unique, candidates = is_unique_solution(temp_clues, all_codes_list, debug=debug)

        # If exactly one candidate remains AND that candidate is the original secret
        if is_still_unique and candidates[0] == secret_code:
             # The clue at index i was redundant, remove it from pruned_clues
             if debug: print(f"DEBUG prune_redundant: Clue #{i+1} IS redundant. Removing it. Unique candidate was {candidates[0]}.")
             pruned_clues.pop(i)
             # DO NOT RESET i - continue checking the next element in the modified list
             # The list length decreased, so the next element is now at index i.
             if debug: print(f"DEBUG prune_redundant: Continuing check with {len(pruned_clues)} clues.")
        else:
             # Clue was necessary, move to the next one by incrementing index
             if debug: print(f"DEBUG prune_redundant: Clue #{i+1} is NOT redundant. Keep it. Unique: {is_still_unique}, Candidate(s): {candidates}")
             i += 1
             
    if debug: print(f"DEBUG prune_redundant: Finished pruning. Final {len(pruned_clues)} clues.")
    return pruned_clues


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate or analyze Mastermind logic puzzles.")
    
    parser.add_argument(
        '--mode', 
        choices=['single', 'all', 'analyze'],
        default='single', 
        help="'single': generate/print one puzzle. 'all': generate all puzzles to YAML. 'analyze': find hardest puzzles from YAML (default: single)"
    )
    parser.add_argument(
        '-c', '--colors', 
        type=int, 
        default=6, 
        help="Number of colors (used in 'single'/'all' modes, informative for 'analyze') (default: 6)"
    )
    parser.add_argument(
        '-p', '--pegs', 
        type=int, 
        default=4, 
        help="Number of pegs (used in 'single'/'all' modes, informative for 'analyze') (default: 4)"
    )
    parser.add_argument(
        '-m', '--max-guesses',
        type=int, 
        default=15, 
        dest='max_guesses_to_generate',
        help="Maximum initial guesses allowed during generation ('all'/'single' modes) (default: 15)"
    )
    parser.add_argument(
        '-o', '--output',
        type=str, 
        default=None, 
        dest='yaml_file',
        help="Output YAML file for 'all' mode (defaults to mastermind_puzzles_C<colors>_P<pegs>.yaml). Input YAML file for 'analyze' mode."
    )
    parser.add_argument(
        '--reveal',
        action='store_true',
        help="Reveal the secret code when using 'single' mode"
    )
    parser.add_argument(
        '--list-hardest',
        action='store_true',
        help="List the secret codes of the hardest puzzles found during 'analyze' mode"
    )
    parser.add_argument(
        '--debug-pruning',
        action='store_true',
        default=False,
        help="Enable detailed debug output during the pruning step."
    )
    
    args = parser.parse_args()

    # Determine output/input filename based on mode
    if args.mode == 'all':
        if args.yaml_file is None:
             args.yaml_file = f"mastermind_puzzles_C{args.colors}_P{args.pegs}.yaml"
    elif args.mode == 'analyze':
        if args.yaml_file is None:
            # Input file is required for analysis
            parser.error("--output/--yaml_file argument is required for --mode analyze")
            
    return args


def print_puzzle(clues, colors, pegs, secret_code=None):
    """Prints the generated puzzle clues to the console."""
    num_to_color_char = {i: chr(ord('A') + i) for i in range(colors)}

    print(f"\n--- Mastermind Puzzle ({colors} colors, {pegs} pegs) ---")
    if secret_code is not None:
        secret_str = ''.join([num_to_color_char.get(c, str(c)) for c in secret_code])
        print(f"Secret Code (revealed): {secret_str}")
    
    print("Clues:")
    for guess, (black, white) in clues:
        guess_str = ''.join([num_to_color_char.get(c, str(c)) for c in guess])
        print(f"  Guess: {guess_str} -> Feedback: {black} Black, {white} White")
    print("----------------------------------------")

def generate_single_puzzle(colors, pegs, max_guesses, debug_pruning):
    """Generates a single Mastermind puzzle with minimal clues."""
    print(f"Generating all possible codes ({colors}^{pegs} = {colors**pegs})...")
    all_codes_list = all_codes(colors, pegs)
    
    secret_code = random.choice(all_codes_list)
    print(f"Chosen secret code: {secret_code} (will be converted to letters for display)")
    
    print(f"Finding initial set of clues to uniquely identify {secret_code} (max {max_guesses} guesses)...")
    try:
        clues = find_solution_clues(secret_code, all_codes_list, max_guesses)
        print(f"Found initial {len(clues)} clues.")
    except ValueError as e:
        print(f"Error: {e}")
        return None, None

    print(f"Pruning redundant clues (debug_pruning={debug_pruning})...")
    pruned_clues = prune_redundant(clues, all_codes_list, secret_code, debug=debug_pruning)
    print(f"Pruned to {len(pruned_clues)} clues.")
    
    return secret_code, pruned_clues

def run_single_mode(args):
    """Handles the 'single' mode of operation."""
    print("Running in SINGLE puzzle generation mode.")
    secret_code, clues = generate_single_puzzle(
        args.colors,
        args.pegs,
        args.max_guesses_to_generate,
        args.debug_pruning
    )
    if clues:
        if args.reveal:
            print_puzzle(clues, args.colors, args.pegs, secret_code=secret_code)
        else:
            print_puzzle(clues, args.colors, args.pegs)
    else:
        print("Could not generate a valid puzzle with the given parameters.")

def generate_and_format_puzzle_data(secret_code, all_codes_list, max_guesses, debug_pruning):
    """Generates a puzzle and formats it for YAML output."""
    try:
        initial_clues = find_solution_clues(secret_code, all_codes_list, max_guesses)
        pruned_clues = prune_redundant(initial_clues, all_codes_list, secret_code, debug_pruning)
        
        # Format clues for YAML (convert tuples to lists if preferred for YAML readability)
        formatted_clues = []
        for guess, (black, white) in pruned_clues:
            formatted_clues.append({
                'guess': list(guess), 
                'feedback': {'black': black, 'white': white}
            })
        
        return {
            'secret_code': list(secret_code),
            'clues': formatted_clues
        }
    except ValueError as e:
        # print(f"Skipping secret {secret_code} due to error: {e}") # Can be too verbose for 'all'
        return None # Indicate failure

def write_puzzles_to_yaml(puzzles, filename):
    """Writes a list of puzzle data to a YAML file."""
    print(f"Writing {len(puzzles)} puzzles to {filename}...")
    try:
        with open(filename, 'w') as f:
            yaml.dump(puzzles, f, indent=2, sort_keys=False)
        print("Successfully wrote puzzles to YAML.")
    except Exception as e:
        print(f"Error writing to YAML file {filename}: {e}")

def run_all_mode(args):
    """Handles the 'all' mode: generates puzzles for all secrets and saves to YAML."""
    print(f"Running in ALL puzzles generation mode for {args.colors} colors, {args.pegs} pegs.")
    print(f"Maximum initial guesses for generation: {args.max_guesses_to_generate}")
    print(f"Debug pruning: {args.debug_pruning}")
    print(f"Output will be saved to: {args.yaml_file}")

    all_codes_list = all_codes(args.colors, args.pegs)
    total_codes = len(all_codes_list)
    print(f"Total possible secret codes: {total_codes}")
    
    generated_puzzles = []
    skipped_count = 0

    for i, secret in enumerate(all_codes_list):
        if (i + 1) % 10 == 0 or i == total_codes - 1:
            print(f"Processing secret code {i+1}/{total_codes}: {secret}...")
        
        puzzle_data = generate_and_format_puzzle_data(
            secret,
            all_codes_list,
            args.max_guesses_to_generate,
            args.debug_pruning
        )
        if puzzle_data:
            generated_puzzles.append(puzzle_data)
        else:
            skipped_count +=1
            # More detailed logging could be added here if needed, e.g., for specific errors
            if (i + 1) % 10 == 0 or i == total_codes - 1: # Log skips periodically
                 print(f"Note: Skipped {skipped_count} codes so far due to generation issues (e.g., couldn't isolate). Secret: {secret}")

    if generated_puzzles:
        write_puzzles_to_yaml(generated_puzzles, args.yaml_file)
        print(f"Successfully generated and saved {len(generated_puzzles)} puzzles.")
    else:
        print("No puzzles were successfully generated.")
    
    if skipped_count > 0:
        print(f"Total codes skipped due to generation issues: {skipped_count}")

def read_puzzles_from_yaml(filename):
    """Reads puzzle data from a YAML file."""
    print(f"Reading puzzles from {filename}...")
    try:
        with open(filename, 'r') as f:
            puzzles = yaml.safe_load(f)
        if not puzzles:
            print("Warning: YAML file is empty or does not contain valid puzzle data.")
            return []
        # Basic validation: check if it's a list and if items have 'clues' and 'secret_code'
        if not isinstance(puzzles, list) or not all('clues' in p and 'secret_code' in p for p in puzzles):
            print("Warning: YAML data does not seem to be in the expected list of puzzles format.")
            # Return empty or raise error depending on how strict we need to be
            return [] 
        print(f"Successfully read {len(puzzles)} puzzles from YAML.")
        return puzzles
    except FileNotFoundError:
        print(f"Error: YAML file {filename} not found.")
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filename}: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while reading {filename}: {e}")
        return []

def analyze_puzzles(all_puzzles):
    """Finds the puzzle(s) with the minimum number of clues."""
    if not all_puzzles:
        return float('inf'), []

    min_clues_count = float('inf')
    hardest_puzzles_details = [] # Store (secret_code, num_clues)

    for puzzle_data in all_puzzles:
        num_clues = len(puzzle_data.get('clues', []))
        secret_code = tuple(puzzle_data.get('secret_code', [])) # Convert to tuple for hashability if needed
        
        if num_clues < min_clues_count:
            min_clues_count = num_clues
            hardest_puzzles_details = [(secret_code, num_clues)]
        elif num_clues == min_clues_count:
            hardest_puzzles_details.append((secret_code, num_clues))
            
    return min_clues_count, hardest_puzzles_details

def print_analysis_results(min_clues, hardest_puzzles, list_details):
    """Prints the results of the puzzle analysis."""
    if min_clues == float('inf'):
        print("No puzzles found or analyzed.")
        return

    print(f"\n--- Puzzle Analysis Results ---")
    print(f"Minimum number of clues found in any puzzle: {min_clues}")
    print(f"Number of puzzles that have this minimum number of clues: {len(hardest_puzzles)}")

    if list_details and hardest_puzzles:
        print("\nSecret codes of the hardest puzzles (those with the minimum number of clues):")
        for secret, num_c in hardest_puzzles:
            print(f"  Secret: {secret} (requires {num_c} clues)")
    print("----------------------------------------")

def run_analyze_mode(args):
    """Handles the 'analyze' mode: reads puzzles from YAML and finds the hardest."""
    print(f"Running in ANALYSIS mode. Reading puzzles from: {args.yaml_file}")
    all_puzzles_data = read_puzzles_from_yaml(args.yaml_file)
    
    if not all_puzzles_data:
        print("No puzzle data to analyze. Exiting.")
        return

    min_clues_val, hardest_puzzles_list = analyze_puzzles(all_puzzles_data)
    print_analysis_results(min_clues_val, hardest_puzzles_list, args.list_hardest)


def main():
    """Main function to drive the puzzle generator/analyzer."""
    args = parse_arguments()

    if args.mode == 'single':
        run_single_mode(args)
    elif args.mode == 'all':
        run_all_mode(args)
    elif args.mode == 'analyze':
        run_analyze_mode(args)
    else:
        print(f"Error: Unknown mode '{args.mode}'. Should not happen due to choices in argparse.")

if __name__ == "__main__":
    main() 
