import json
import random

def main():
    mcq_file = 'mcq_data.json'
    other_file = 'other_data.json'
    
    print(f"Loading data from {mcq_file} and {other_file}...")
    
    # Load mcq data
    with open(mcq_file, 'r', encoding='utf-8') as f:
        mcq_data = json.load(f)
        
    # Load other data
    with open(other_file, 'r', encoding='utf-8') as f:
        other_data = json.load(f)

    if not other_data:
        print("No new data found to insert.")
        return

    original_length = len(mcq_data)
    new_length = len(other_data)
    
    # Calculate the 90% boundary based on the mcq data size
    current_limit = int(original_length * 0.90)
    
    # We want to place the new items in the first 90% of the mcq data,
    # starting after the 5th item.
    # To preserve their existing order, we generate sorted random indices.
    start_index = min(5, current_limit)
    insert_positions = sorted([random.randint(start_index, current_limit) for _ in range(new_length)])
    
    for i, item in enumerate(other_data):
        # Add `i` to account for the array shifting right after each insertion
        mcq_data.insert(insert_positions[i] + i, item)

    # Save the updated data back to mcq_data.json
    # (The existing items remain completely unchanged, just shifted)
    print(f"Saving merged data back to {mcq_file}...")
    with open(mcq_file, 'w', encoding='utf-8') as f:
        json.dump(mcq_data, f, indent=4)
        
    print(f"Successfully inserted {new_length} other items into the first 90% of {mcq_file}.")
    print(f"Original size: {original_length} | New size: {len(mcq_data)}")

if __name__ == '__main__':
    main()
