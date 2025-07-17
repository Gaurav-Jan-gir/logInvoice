"""
Write a Python script called analyze_dir.py that takes a directory path as a command-line argument using sys.argv. The script should:
	List all files (ignore folders) inside the given directory.
	Calculate the total number of files.
	Identify the file with the longest name (based on character count).
	Calculate the square root of the total number of files (rounded to 2 decimal places).
	Round the file count up to the nearest multiple of 10 using math.ceil().
	Print the names of all files.
	Display the longest filename.
	Print total files, square root, and rounded value.
	Catch cases where the path doesn’t exist.
	Show a proper usage message if no path is given.
"""

import os
import sys
import math
from pathlib import Path
def analyze_directory(directory_path):
    try:
        # List all files in the directory
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        
        # Calculate total number of files
        total_files = len(files)
        
        # Identify the file with the longest name
        longest_file = max(files, key=len) if files else ""
        
        # Calculate square root of total files, rounded to 2 decimal places
        square_root = round(math.sqrt(total_files), 2)
        
        # Round total files up to the nearest multiple of 10
        rounded_total = math.ceil(total_files / 10) * 10
        
        # Print results
        print("Files in directory:")
        for file in files:
            print(file)
        
        print(f"\nLongest filename: {longest_file}")
        print(f"Total files: {total_files}")
        print(f"Square root of total files (rounded): {square_root}")
        print(f"Rounded total files to nearest multiple of 10: {rounded_total}")
    
    except FileNotFoundError:
        print(f"Error: The path '{directory_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_dir.py <directory_path>")
        sys.exit(1)

    dir_path = sys.argv[1]
    analyze_directory(dir_path)