import os
import sys
from objects import read_blob_object, write_tree, write_commit, hash_object, read_tree_object
from packfile import clone_repo

def init_repo():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")
        
def cat_file():
    blob = sys.argv[sys.argv.index("-p") + 1]
    (type, content) = read_blob_object(blob)
    print(content, end="")
        
def hash_object_command():
    file = sys.argv[sys.argv.index("-w") + 1]
    with open(file, "rb") as file:
        data = file.read()
    sha = hash_object(data, "blob", True)
    print(sha)
    
def ls_tree():    
    tree_sha = sys.argv[sys.argv.index("--name-only") + 1]
    entries = read_tree_object(tree_sha)
    for entry in entries:
        print(entry['name'])
            
def write_tree_command():
    working_dir = os.getcwd()
    tree_sha = write_tree(working_dir)
    print(tree_sha)
    
def commit_tree():
    tree_sha = sys.argv[sys.argv.index("commit-tree") + 1]
    parent_commit_sha = sys.argv[sys.argv.index("-p") + 1]
    commit_message = sys.argv[sys.argv.index("-m") + 1]
    commit_sha = write_commit(tree_sha, parent_commit_sha, commit_message)
    print(commit_sha)

def clone_command():
    git_url, dir = sys.argv[sys.argv.index("clone") + 1:]
    print(f"git_url: {git_url}\n dir: {dir}")
    clone_repo(git_url, dir)