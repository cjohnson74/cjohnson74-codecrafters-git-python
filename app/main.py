import sys
import os
import zlib
from commands import init_repo, cat_file, hash_object_command, ls_tree, write_tree_command, commit_tree, clone_command

def main():
    commands = {
        "init": init_repo,
        "cat-file": cat_file,
        "hash-object": hash_object_command,
        "ls-tree": ls_tree,
        "write-tree": write_tree_command,
        "commit-tree": commit_tree,
        "clone": clone_command,
    }
    
    command = sys.argv[1]
    if command in commands:
        commands[command]()
    else:
        raise RuntimeError(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
