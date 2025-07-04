#!/usr/bin/env python3
"""
Test script to create a folder structure for testing the tree diagram visualization.
"""

import os
import sys

def create_folder_structure():
    """Create the test folder structure"""
    
    # Define the folder structure with text file content
    structure = {
        "Airframe": {
            "Wing": {
                "Spars": {"spar_design.txt": "Wing spar design specifications and load calculations"},
                "Ribs": {"rib_layout.txt": "Wing rib layout and structural analysis"}
            },
            "Tail": {
                "Spars": {"tail_spar_notes.txt": "Tail spar design and stress analysis"},
                "Ribs": {"tail_rib_specs.txt": "Tail rib specifications and manufacturing notes"}
            },
            "Fuselage": {
                "Frames": {"frame_design.txt": "Fuselage frame design and structural requirements"},
                "Longeron": {"longeron_specs.txt": "Longeron specifications and load distribution"}
            }
        }
    }
    
    def create_folders_recursive(base_path, folders):
        """Recursively create folders and files"""
        for folder_name, contents in folders.items():
            folder_path = os.path.join(base_path, folder_name)
            
            # Create the folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"Created: {folder_path}")
            else:
                print(f"Already exists: {folder_path}")
            
            # Create text files in this folder
            for filename, content in contents.items():
                if isinstance(content, str):  # This is a file
                    file_path = os.path.join(folder_path, filename)
                    if not os.path.exists(file_path):
                        with open(file_path, 'w') as f:
                            f.write(content)
                        print(f"  Created file: {filename}")
                    else:
                        print(f"  File already exists: {filename}")
                elif isinstance(content, dict):  # This is a subfolder
                    create_folders_recursive(folder_path, content)
    
    # Get the current directory
    current_dir = os.getcwd()
    print(f"Creating folder structure in: {current_dir}")
    print("-" * 50)
    
    # Create the folder structure
    create_folders_recursive(current_dir, structure)
    
    print("-" * 50)
    print("Folder structure created successfully!")
    print("\nStructure created:")
    print("Airframe/")
    print("├── Wing/")
    print("│   ├── Spars/")
    print("│   │   └── spar_design.txt")
    print("│   └── Ribs/")
    print("│       └── rib_layout.txt")
    print("├── Tail/")
    print("│   ├── Spars/")
    print("│   │   └── tail_spar_notes.txt")
    print("│   └── Ribs/")
    print("│       └── tail_rib_specs.txt")
    print("└── Fuselage/")
    print("    ├── Frames/")
    print("    │   └── frame_design.txt")
    print("    └── Longeron/")
    print("        └── longeron_specs.txt")

def cleanup_test_structure():
    """Remove the test folder structure"""
    import shutil
    
    airframe_path = os.path.join(os.getcwd(), "Airframe")
    if os.path.exists(airframe_path):
        shutil.rmtree(airframe_path)
        print(f"Removed test structure: {airframe_path}")
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