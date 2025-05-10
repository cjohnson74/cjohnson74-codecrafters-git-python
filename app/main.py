import ssl
import sys
import os
import zlib
import hashlib
from datetime import datetime
import socket
from urllib.parse import urlparse

USER_NAME="cjohnson74"
USER_EMAIL="cjohnson74.tech@gmail.com"

def read_blob_object(sha):
    folder = sha[:2]
    file = sha[2:]
    with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
        contents = blob_file.read()
        contents = zlib.decompress(contents).decode("utf-8")
        type = contents.split(" ")[0]
        content = contents.split("\0")[1]
        return (type, content)
    
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

def fetch_pack_file(head_sha, git_url):
    host = "github.com"
    port = 443
    parsed_url = urlparse(git_url)
    repo_path = parsed_url.path
    
    body = (
        f"0054want {head_sha} multiack side-band-64k ofs-delta\n"
        f"0000"
        f"0009done\n"
    )
    print(f"pkt_line: {body}")
    
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port)) as client_socket:
            with context.wrap_socket(client_socket, server_hostname=host) as client_secure_socket:
                request = (
                    f"POST {repo_path}/git-upload-pack HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"Accept: */*\r\n"
                    f"User-Agent: custom-git-client\r\n"
                    f"Accept: */*\r\n"
                    f"Content-Type: application/x-git-upload-pack-request\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Connection: close\r\n\r\n"
                )
                request = request.encode("utf-8") + body.encode("utf-8")
                client_secure_socket.sendall(request)
                
                res = bytearray()
                while True:
                    data = client_secure_socket.recv(4096)
                    if not data:
                        break
                    res.extend(data)
    except (socket.error, ssl.SSLError) as e:
        raise RuntimeError(f"Failed to send request to {host}:{port} - {e}")
    
    print(f"Response: {res}")

def fetch_head_sha(git_url):
    host = "github.com"
    port = 443
    parsed_url = urlparse(git_url)
    repo_path = parsed_url.path
    
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port)) as client_socket:
            with context.wrap_socket(client_socket, server_hostname=host) as client_secure_socket:
                request = (
                    f"GET {repo_path}/info/refs?service=git-upload-pack HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"User-Agent: custom-git-client\r\n"
                    f"Accept: */*\r\n"
                    f"Connection: close\r\n\r\n"
                )
                client_secure_socket.sendall(request.encode("utf-8"))
                
                res = bytearray()
                while True:
                    data = client_secure_socket.recv(4096)
                    if not data:
                        break
                    res.extend(data)
    except (socket.error, ssl.SSLError) as e:
        raise RuntimeError(f"Failed to send request to {host}:{port} - {e}")
    
    print(f"Res: {res}")
    headers, _, body = res.partition(b"\r\n\r\n")
    body = body.decode("utf-8")
    print(f"Body: {body}")
    head_sha = body[body.index("0155")+4:body.index("HEAD")-1]
    return head_sha

def clone_repo(git_url, dir):
    head_sha = fetch_head_sha(git_url)
    print(f"head_sha: {head_sha}")
    pack_file = fetch_pack_file(head_sha, git_url)
    

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
        with open(file, "rb") as file:
            data = file.read()
        sha = hash_object(data, "blob", True)
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
    elif command == "commit-tree":
        tree_sha = sys.argv[sys.argv.index(command) + 1]
        parent_commit_sha = sys.argv[sys.argv.index("-p") + 1]
        commit_message = sys.argv[sys.argv.index("-m") + 1]
        commit_sha = write_commit(tree_sha, parent_commit_sha, commit_message)
        print(commit_sha)
    elif command == "clone":
        git_url, dir = sys.argv[sys.argv.index(command) + 1:]
        print(f"git_url: {git_url}\n dir: {dir}")
        clone_repo(git_url, dir)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
