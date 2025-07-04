from rich.tree import Tree
from rich.console import Console
import os

def build_tree(directory, tree):
    for entry in sorted(os.listdir(directory)):
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            branch = tree.add(f"[bold blue]{entry}[/]")
            build_tree(path, branch)
        # else:  # Skip files
        #     pass

if __name__ == "__main__":
    console = Console()
    root_dir = "."
    tree = Tree(f"[bold magenta]{os.path.basename(os.path.abspath(root_dir))}[/]")
    build_tree(root_dir, tree)
    console.print(tree)