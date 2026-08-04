import json
import random

def main():
    original_file = 'original_data.json'
    new_file = 'new_data.json'
    
    print(f"Loading data from {original_file} and {new_file}...")
    
    # Load original data
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
        
    # Load new data
    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    if not new_data:
        print("No new data found to insert.")
        return

    original_length = len(original_data)
    new_length = len(new_data)
    
    # Calculate the 75% boundary based on the original size of the array
    current_limit = int(original_length * 0.75)
    
    # We want to place the new items in the first 75% of the original data,
    # starting after the 5th item.
    # To preserve their existing order, we generate sorted random indices.
    start_index = min(5, current_limit)
    insert_positions = sorted([random.randint(start_index, current_limit) for _ in range(new_length)])
    
    for i, item in enumerate(new_data):
        # Add `i` to account for the array shifting right after each insertion
        original_data.insert(insert_positions[i] + i, item)

    # Save the updated data back to original_data.json
    # (The existing items remain completely unchanged, just shifted)
    print(f"Saving merged data back to {original_file}...")
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, indent=4)
        
    print(f"Successfully inserted {new_length} new items into the first 75% of {original_file}.")
    print(f"Original size: {original_length} | New size: {len(original_data)}")

if __name__ == '__main__':
    main()
