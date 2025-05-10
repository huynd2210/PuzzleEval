import sys
import os
from typing import List, Set, Tuple, Optional

# --- Word List Loading and Caching ---

# Define expected filenames relative to the script location or workspace root
WORD_LIST_FILES = {
    3: "three_letter_words.txt",
    4: "four_letter_words.txt",
    5: "five_letter_words.txt"
}

_word_list_cache: dict[int, Optional[Set[str]]] = {}

def load_word_list(length: int) -> Optional[Set[str]]:
    """Loads the word list for the specified length, using a cache."""
    if length in _word_list_cache:
        return _word_list_cache[length]

    if length not in WORD_LIST_FILES:
        print(f"Error: No word list defined for length {length}.", file=sys.stderr)
        _word_list_cache[length] = None
        return None

    file_path = WORD_LIST_FILES[length]
    word_set: Set[str] = set()

    if not os.path.exists(file_path):
        print(f"Error: Word list file not found: {file_path}", file=sys.stderr)
        print("Please ensure the required Collins Scrabble word list files are present:", file=sys.stderr)
        print(f"  - {WORD_LIST_FILES[3]} (for 3-letter words)", file=sys.stderr)
        print(f"  - {WORD_LIST_FILES[4]} (for 4-letter words)", file=sys.stderr)
        _word_list_cache[length] = None
        return None

    try:
        print(f"Loading word list: {file_path} ...", file=sys.stderr) # Info message
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().upper()
                if len(word) == length:
                    word_set.add(word)
        print(f"Loaded {len(word_set)} words of length {length}.", file=sys.stderr)
        _word_list_cache[length] = word_set
        return word_set
    except Exception as e:
        print(f"Error reading word list file {file_path}: {e}", file=sys.stderr)
        _word_list_cache[length] = None
        return None

# --- Validation Logic ---

def words_differ_by_one(word1: str, word2: str) -> bool:
    """Checks if two words of the same length differ by exactly one character."""
    if len(word1) != len(word2):
        return False
    diff_count = 0
    for char1, char2 in zip(word1, word2):
        if char1 != char2:
            diff_count += 1
            if diff_count > 1:
                return False
    return diff_count == 1

def is_valid_ladder(attempt: List[str]) -> Tuple[bool, str]:
    """
    Validates a word ladder attempt using Collins Scrabble lists (3 or 4 letters).

    Args:
        attempt: A list of strings representing the proposed word ladder.

    Returns:
        A tuple containing:
          - bool: True if the ladder is valid, False otherwise.
          - str: A message indicating success or the reason for failure.
    """
    if not attempt:
        return False, "Attempt is empty."

    # Convert attempt to uppercase
    attempt_upper = [word.upper() for word in attempt]

    if len(attempt_upper) < 2:
        return False, "Attempt needs at least two words to be a ladder."

    # Determine required word length and load word list
    first_word = attempt_upper[0]
    word_len = len(first_word)

    accepted_words = load_word_list(word_len)
    if accepted_words is None:
        return False, f"Cannot validate: Failed to load or find word list for length {word_len}."

    # 1. Check word validity (length consistency and presence in list)
    if first_word not in accepted_words:
        return False, f"Invalid start word: '{first_word}' not in {word_len}-letter word list."

    for i, word in enumerate(attempt_upper[1:], start=1):
        if len(word) != word_len:
             # This check might be redundant if list loading enforces length, but good sanity check
             return False, f"Word length mismatch: '{attempt_upper[i-1]}' vs '{word}'. All words must have length {word_len}."
        if word not in accepted_words:
            return False, f"Invalid word: '{word}' at step {i+1} not in {word_len}-letter word list."

    # 2. Check step validity
    for i in range(len(attempt_upper) - 1):
        word1 = attempt_upper[i]
        word2 = attempt_upper[i+1]
        if not words_differ_by_one(word1, word2):
            return False, f"Invalid step: '{word1}' -> '{word2}' differ by more than one letter."

    # If all checks pass
    return True, "Ladder is valid."

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    print("--- Running Validation Tests (using Collins lists) ---")

    # Ensure word list files exist before running tests that need them
    # You might need to adjust paths or ensure files are in the right place
    print("Checking for required word list files...")
    files_ok = True
    for length, filename in WORD_LIST_FILES.items():
        if not os.path.exists(filename):
            print(f"  Missing: {filename} (for {length}-letter words)")
            files_ok = False
        else:
            print(f"  Found: {filename}")

    if not files_ok:
        print("\nPlease place the required word list files in the same directory as the script.")
        print("Exiting example tests.")
        sys.exit(1)

    # Test cases (assuming word lists are present)
    test_ladders = {
        "Valid 3-Letter": ["CAT", "COT", "COG", "DOG"],      # Should be valid if lists ok
        "Valid 4-Letter": ["COLD", "CORD", "WORD", "WARD"], # Should be valid if lists ok
        "Invalid Word (3)": ["CAT", "COT", "CXT", "COG"], # CXT likely invalid
        "Invalid Word (4)": ["FOUR", "FOUL", "FOLL", "FALL"], # FOLL likely invalid
        "Invalid Step (3)": ["APE", "APT", "OPT"],        # APE -> APT ok, APT -> OPT ok ? (Check list) APE -> OPT invalid step
        "Invalid Step (4)": ["READ", "ROAD", "ROAM"],    # READ -> ROAD ok, ROAD -> ROAM ok? READ -> ROAM invalid step
        "Length Mismatch": ["CAT", "CATS"],              # Should fail
        "Unsupported Length": ["APPLE", "APPLY"],         # Should fail (len 5)
        "Empty": [],
    }

    print("\nRunning tests...")
    sys.stdout.flush() # Explicitly flush buffer
    for name, ladder_attempt in test_ladders.items():
        # Clear cache before each test if you want to see loading messages each time
        # _word_list_cache = {} # Uncomment for debugging loading
        print(f"\nTest '{name}':")
        sys.stdout.flush() # Explicitly flush buffer
        print(f"  Attempt: {ladder_attempt}")
        sys.stdout.flush() # Explicitly flush buffer
        is_valid, message = is_valid_ladder(ladder_attempt)
        print(f"  Result: {'Valid' if is_valid else 'Invalid'}")
        sys.stdout.flush() # Explicitly flush buffer
        print(f"  Message: {message}")
        sys.stdout.flush() # Explicitly flush buffer

    print("\n--- All Tests Complete ---")
    sys.stdout.flush() # Explicitly flush buffer 