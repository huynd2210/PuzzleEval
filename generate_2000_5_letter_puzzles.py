import csv
import itertools
import os
import string 
from collections import deque 
import time 
import random # For potentially shuffling if needed, but will use combinations first

def load_words_from_file(filepath):
    """Loads words from a file, strips whitespace, and converts to uppercase. Returns a set."""
    words = set()
    try:
        with open(filepath, 'r') as f:
            for line in f:
                word = line.strip().upper()
                if word: 
                    words.add(word)
    except FileNotFoundError:
        print(f"Error: Word file '{filepath}' not found.")
        return None
    return words 

def get_neighbors(word, word_set):
    """Find all valid one-letter-different neighbors of a word."""
    neighbors = set()
    alphabet = string.ascii_uppercase
    for i in range(len(word)):
        original_char = word[i]
        for char in alphabet:
            if char == original_char:
                continue
            new_word = word[:i] + char + word[i+1:]
            if new_word in word_set:
                neighbors.add(new_word)
    return neighbors

def build_adjacency_list(word_set, word_length_for_logging):
    """Precompute the adjacency list for the word graph."""
    print(f"Building adjacency list for {word_length_for_logging}-letter words...")
    start_build_time = time.time()
    adj_list = {word: get_neighbors(word, word_set) for word in word_set}
    end_build_time = time.time()
    print(f"Adjacency list built for {len(word_set)} {word_length_for_logging}-letter words in {end_build_time - start_build_time:.2f}s.")
    return adj_list

def find_ladder_path(start_word, end_word, word_list_set, adjacency_list, max_path_len=15):
    """Find the shortest word ladder using BFS."""
    if start_word == end_word:
        return [start_word] # Technically a ladder of one

    # Assuming start_word and end_word are already validated to be in word_list_set by the caller if needed
    # or that word_list_set is the definitive source passed to adj_list building.
    if start_word not in adjacency_list or end_word not in adjacency_list:
         # If they weren't part of the set for which adj_list was built, no path possible through it.
        return None
        
    queue = deque([[start_word]])
    visited = {start_word}
    
    while queue:
        current_path = queue.popleft()
        
        if len(current_path) > max_path_len:
            continue

        last_word = current_path[-1]

        if last_word == end_word:
            return current_path

        # adj_list.get(last_word, set()) is crucial if last_word might not be in adj_list
        # (e.g. if adj_list was built from a subset not containing last_word for some reason)
        # However, if adj_list is built from the full target_letter_words_set, this should be fine.
        for neighbor in adjacency_list.get(last_word, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = list(current_path) 
                new_path.append(neighbor)
                queue.append(new_path)
    return None

def main():
    target_word_length = 5
    puzzles_to_generate = 2000
    word_file_relative_path = os.path.join('word_ladder', 'five_letter_words_common.txt')
    output_csv_file = f'word_ladder_puzzles_{target_word_length}_letter_{puzzles_to_generate}.csv' 

    script_dir = os.path.dirname(os.path.abspath(__file__))
    word_file_abs_path = os.path.join(script_dir, word_file_relative_path)
    output_csv_abs_path = os.path.join(script_dir, output_csv_file)

    print(f"Loading words from: {word_file_abs_path}")
    all_words_from_file = load_words_from_file(word_file_abs_path) 

    if not all_words_from_file:
        print("Could not load words. Exiting.")
        return

    target_letter_words_set = {word for word in all_words_from_file if len(word) == target_word_length}
    if not target_letter_words_set:
        print(f"No {target_word_length}-letter words found. Exiting.")
        return
    
    if len(target_letter_words_set) < 2:
        print(f"Need at least 2 words of length {target_word_length} to generate pairs. Found {len(target_letter_words_set)}. Exiting.")
        return
        
    print(f"Found {len(target_letter_words_set)} {target_word_length}-letter words.")
    sorted_target_words = sorted(list(target_letter_words_set)) # For consistent pair generation

    adjacency_list = build_adjacency_list(target_letter_words_set, target_word_length)

    # Generate all possible pairs first
    print(f"Generating all unique {target_word_length}-letter word pairs for shuffling...")
    all_possible_pairs = list(itertools.combinations(sorted_target_words, 2))
    print(f"Generated {len(all_possible_pairs)} total unique pairs.")
    
    # Shuffle the list of all pairs
    print("Shuffling pairs...")
    random.shuffle(all_possible_pairs)
    print("Pairs shuffled.")

    question_template = f"Solve this word ladder puzzle ({{}} -> {{}}). Accepted word list from source: @https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt"
    
    collected_puzzles = []
    pairs_processed_count = 0
    
    print(f"Attempting to generate {puzzles_to_generate} {target_word_length}-letter word ladder puzzles...")
    generation_start_time = time.time()

    # Iterate through the SHUFFLED list of all possible pairs
    for start_word, end_word in all_possible_pairs:
        pairs_processed_count += 1
        if len(collected_puzzles) >= puzzles_to_generate:
            break # Stop if we have enough puzzles

        path = find_ladder_path(start_word, end_word, target_letter_words_set, adjacency_list)
        
        if path:
            question = question_template.format(start_word, end_word)
            answer_str = " -> ".join(path)
            collected_puzzles.append({'question': question, 'answer': answer_str})
            if len(collected_puzzles) % 100 == 0: # Print progress every 100 found puzzles
                print(f"  Collected {len(collected_puzzles)}/{puzzles_to_generate} puzzles... (Processed {pairs_processed_count} pairs)")
    
    generation_end_time = time.time()
    print(f"\nFinished attempt to generate puzzles in {generation_end_time - generation_start_time:.2f} seconds.")
    print(f"Collected {len(collected_puzzles)} puzzles after processing {pairs_processed_count} pairs.")

    if not collected_puzzles:
        print("No puzzles could be generated.")
        return

    print(f"Writing {len(collected_puzzles)} puzzles to {output_csv_abs_path}")
    try:
        with open(output_csv_abs_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['question', 'answer']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(collected_puzzles)
        print(f"Successfully generated CSV file: {output_csv_abs_path}")
    except IOError as e:
        print(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main() 