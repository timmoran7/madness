import os
import re

# Define the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define folders and their prefixes to remove
folders = {
    'fourFactors': 'fourFactors',
    'miscStats': 'misc',
    'matchups': 'matchups',
    'upsets': 'upsets'
}

def rename_files():
    for folder, prefix in folders.items():
        folder_path = os.path.join(base_dir, folder)
        
        if not os.path.exists(folder_path):
            print(f"Folder {folder} does not exist, skipping...")
            continue
        
        # Get all JSON files in the folder
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        
        for filename in files:
            # Check if filename starts with the prefix followed by a year
            pattern = f'^{prefix}(\\d{{4}})\\.json$'
            match = re.match(pattern, filename)
            
            if match:
                year = match.group(1)
                new_filename = f"{year}.json"
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_filename)
                
                # Rename the file
                os.rename(old_path, new_path)
                print(f"Renamed: {folder}/{filename} -> {folder}/{new_filename}")
            else:
                print(f"Skipped: {folder}/{filename} (already in correct format or doesn't match pattern)")

if __name__ == "__main__":
    print("Starting file renaming process...")
    rename_files()
    print("Done!")
