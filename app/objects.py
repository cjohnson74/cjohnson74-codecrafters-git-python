from datetime import datetime
import os
import zlib
import hashlib

USER_NAME="cjohnson74"
USER_EMAIL="cjohnson74.tech@gmail.com"

def hash_object(data, obj_type="blob", write=True):
    header = f"{obj_type} {len(data)}\0".encode()
    # print(header)
    full_data = header + data
    # print(full_data)
    sha = hashlib.sha1(full_data).hexdigest()
    
    if write:
        object_dir = os.path.join(".git", "objects", sha[:2])
        object_path = os.path.join(object_dir, sha[2:])
        if not os.path.exists(object_path):
            os.makedirs(object_dir, exist_ok=True)
            with open(object_path, "wb") as file:
                file.write(zlib.compress(full_data))
    return sha

def read_blob_object(sha):
    folder = sha[:2]
    file = sha[2:]
    with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
        contents = blob_file.read()
        contents = zlib.decompress(contents).decode("utf-8")
        type = contents.split(" ")[0]
        content = contents.split("\0")[1]
        return (type, content)

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

def write_tree(directory):
    entries = []
    for entry in sorted(os.listdir(directory)):
        if ".git" in entry:
            continue
        entry_path = os.path.join(directory, entry)
        if os.path.isdir(entry_path):
            mode = "40000"
            sha = write_tree(entry_path)
        else:
            mode = "100644"
            with open(entry_path, "rb") as file:
                content = file.read()
            sha = hash_object(content, obj_type="blob")
        
        entries.append(f"{mode} {entry}\0".encode() + bytes.fromhex(sha))
        
    tree_content = b"".join(entries)
    return hash_object(tree_content, obj_type="tree")

def write_commit(tree_sha, parent_commit_sha, commit_message):
    current_time = datetime.now()
    data = []
    data = (
        f"tree {tree_sha}\n"
        f"parent {parent_commit_sha}\n"
        f"author {USER_NAME} <{USER_EMAIL}> {int(current_time.timestamp())} {str(current_time.astimezone().tzinfo)}\n"
        f"committer {USER_NAME} <{USER_EMAIL}> {int(current_time.timestamp())} {str(current_time.astimezone().tzinfo)}\n"
        ""
        f"{commit_message}"
        ""
    ).encode("utf-8")
    commit_sha = hash_object(data, obj_type="commit", write=True)
    return commit_sha