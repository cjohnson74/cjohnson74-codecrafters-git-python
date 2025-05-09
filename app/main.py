import sys
import os
import zlib
import hashlib

def read_blob_object(sha):
    folder = sha[:2]
    file = sha[2:]
    with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
        contents = blob_file.read()
        contents = zlib.decompress(contents).decode("utf-8")
        type = contents.split(" ")[0]
        content = contents.split("\0")[1]
        return (type, content)
    
def hash_object(file):
    with open(file) as file:
        data = file.read()
        data_len = len(data)
        blob_object = f"blob {data_len}\0{data}"
        # print(f"data: {data}")
        # print(f"blob_obj: {repr(blob_object)}")
        sha = hashlib.sha1(blob_object.encode("utf-8")).hexdigest()
        file_path = f".git/objects/{sha[:2]}/{sha[2:]}"
        # print(f"file_path: {file_path}")
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(zlib.compress(blob_object.encode("utf-8")))
        return sha
    
def read_tree_object(sha):
    folder = sha[:2]
    file = sha[2:]
    with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
        data = blob_file.read()
        data = zlib.decompress(data)
        null_pos = data.index(b' ')
        content = data[null_pos + 1:]
        
        index = 0
        entries = []
        
        while index < len(content):
            space_pos = content.find(b' ', index)
            file_mode = content[index:space_pos].decode("utf-8")
            index = space_pos + 1
            
            null_pos = content.find(b'\0', index)
            file_name = content[index:null_pos].decode("utf-8")
            index = null_pos + 1
            
            raw_sha = content[index:index + 20]
            sha_hex = raw_sha.hex()
            index += 20
            
            entries.append({
                "mode": file_mode,
                "name": file_name,
                "sha": sha_hex
            })
        return entries
    
def write_tree(dir, visited_dirs=None):
    entries = []
    for entry in sorted(os.listdir(dir)):
        entry_path = os.path.join(dir, entry)
        if os.path.isdir(entry_path):
            mode = "40000"
            sha = write_tree(entry_path)
        else:
            mode = "100644"
            with open(entry_path, "rb") as file:
                content = file.read()
            sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        
        entries.append((mode, entry, bytes.fromhex(sha)))
        
    tree_content = b"".join(
        f"{mode} {name}\0".encode() + sha for mode, name, sha in entries
    )
    tree_header = f"tree {len(tree_content)}\0".encode()
    tree_object = tree_header + tree_content
    
    tree_sha = hashlib.sha1(tree_object).hexdigest()
    
    object_dir = os.path.join(".git", "objects", tree_sha[:2])
    object_path = os.path.join(object_dir, tree_sha[2:])
    os.makedirs(object_dir, exist_ok=True)
    with open(object_path, "wb") as file:
        file.write(tree_object)
    
    return tree_sha
        

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # Uncomment this block to pass the first stage
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file":
        blob = sys.argv[sys.argv.index("-p") + 1]
        (type, content) = read_blob_object(blob)
        print(content, end="")
    elif command == "hash-object":
        file = sys.argv[sys.argv.index("-w") + 1]
        sha = hash_object(file)
        print(sha)
    elif command == "ls-tree":
        tree_sha = sys.argv[sys.argv.index("--name-only") + 1]
        entries = read_tree_object(tree_sha)
        for entry in entries:
            print(entry['name'])
    elif command == "write-tree":
        working_dir = os.getcwd()
        tree_sha = write_tree(working_dir)
        print(tree_sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
