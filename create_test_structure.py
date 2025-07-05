#!/usr/bin/env python3
"""
Test script to create a folder structure for testing the tree diagram visualization.
"""

import os
import sys

def create_folder_structure():
    """Create a 20-level deep test folder structure"""
    current_dir = os.getcwd()
    print(f"Creating 20-level deep folder structure in: {current_dir}")
    print("-" * 50)

    # Build the deep path
    deep_path = current_dir
    for i in range(1, 21):
        folder_name = f"Level{i}"
        deep_path = os.path.join(deep_path, folder_name)
        if not os.path.exists(deep_path):
            os.makedirs(deep_path)
            print(f"Created: {deep_path}")
        else:
            print(f"Already exists: {deep_path}")

    # Create a file at the deepest level
    deep_file = os.path.join(deep_path, "deep_file.txt")
    if not os.path.exists(deep_file):
        with open(deep_file, 'w') as f:
            f.write("This is a file at the deepest (20th) level.")
        print(f"  Created file: {deep_file}")
    else:
        print(f"  File already exists: {deep_file}")

    print("-" * 50)
    print("20-level deep folder structure created successfully!")
    print("\nStructure created:")
    for i in range(1, 21):
        print("    " * (i-1) + f"Level{i}/")
    print("    " * 20 + "deep_file.txt")

def cleanup_test_structure():
    """Remove the test folder structure"""
    import shutil
    
    level1_path = os.path.join(os.getcwd(), "Level1")
    if os.path.exists(level1_path):
        shutil.rmtree(level1_path)
        print(f"Removed test structure: {level1_path}")
    else:
        print("No test structure found to remove.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_test_structure()
    else:
        create_folder_structure()
        print("\nTo run the tree diagram:")
        print("python folder_tree_diagram.py")
        print("\nTo cleanup the test structure:")
        print("python create_test_structure.py --cleanup") 