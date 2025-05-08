import sys
import os
import zlib
import hashlib

def cat_file(blob):
    folder = blob[:2]
    file = blob[2:]
    with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
        contents = blob_file.read()
        contents = zlib.decompress(contents).decode("utf-8")
        type = contents.split(" ")[0]
        content = contents.split("\0")[1]
        return (type, content)
    
def hash_object(file):
    with open(file) as file:
        data = file.read()
        blob_object = f"blob {len(data)}\0{data}"
        sha = hashlib.sha1(blob_object.encode("utf-8")).hexdigest()
        file_path = f".git/objects/{sha[:2]}/{sha[2:]}"
        os.makedirs(os.path.dirname(file_path))
        with open(file_path, "wb") as file:
            file.write(zlib.compress(blob_object.encode("utf-8")))
        return sha
    
def read_tree_object(blob):
    (type, content) = cat_file(blob)
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
        (type, content) = cat_file(blob)
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
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
