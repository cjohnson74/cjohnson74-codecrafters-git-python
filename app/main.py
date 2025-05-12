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
GIT_OBJECT_TYPES = {
    "1": "COMMIT",
    "2": "TREE",
    "3": "BLOB",
    "4": "TAG",
    "6": "OFS_DELTA",
    "7": "REF_DELTA"
}

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

def construct_negotiation_request(head_sha):
    want_line_content = f"want {head_sha} multi_ack side-band-64k ofs-delta\n"
    want_line = f"{len(want_line_content) + 4:04x}{want_line_content}"

    flush_packet = "0000"
    done_line = "0009done\n"

    return want_line + flush_packet + done_line

def fetch_pack_file(git_url):
    port = 443
    parsed_url = urlparse(git_url)
    host = parsed_url.netloc
    repo_path = parsed_url.path
    
    ref_res = get_refs(port, host, repo_path)
    refs = parse_refs(ref_res)
    head_sha = refs["HEAD"]
    
    negotiation_request = construct_negotiation_request(head_sha)
    
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port)) as client_socket:
            with context.wrap_socket(client_socket, server_hostname=host) as client_secure_socket:
                post_request = (
                    f"POST {repo_path}/git-upload-pack HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"User-Agent: custom-git-client\r\n"
                    f"Accept: */*\r\n"
                    f"Content-Type: application/x-git-upload-pack-request\r\n"
                    f"Content-Length: {len(negotiation_request)}\r\n"
                    f"Connection: close\r\n\r\n"
                    f"{negotiation_request}"
                )

                client_secure_socket.sendall(post_request.encode("utf-8"))
                
                packfile_response = bytearray()
                while True:
                    data = client_secure_socket.recv(4096)
                    if not data:
                        break
                    packfile_response.extend(data)   
                               
    except (socket.error, ssl.SSLError) as e:
        raise RuntimeError(f"Failed to send request to {host}:{port} - {e}") from e
    
    return packfile_response

def get_refs(port, host, repo_path):
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
                
                ref_res = bytearray()
                while True:
                    data = client_secure_socket.recv(4096)
                    if not data:
                        break
                    ref_res.extend(data)
                    
    except (socket.error, ssl.SSLError) as e:
        raise RuntimeError(f"Failed to send request to {host}:{port} - {e}") from e
    
    return ref_res
    
def decode_ref_res(body):
    decoded_body = b""
    while body:
        chunk_size_end = body.find(b"\r\n")
        if chunk_size_end == -1:
            break
        chunk_size = int(body[:chunk_size_end].decode("utf-8"), 16)
        if chunk_size == 0:
            break
        chunk_start = chunk_size_end + 2
        chunk_end = chunk_start + chunk_size
        decoded_body += body[chunk_start:chunk_end]
        body = body[chunk_end + 2:]
    
    return decoded_body

def parse_refs(ref_res):
    headers, _, body = ref_res.partition(b'\r\n\r\n')
    decoded_body = decode_ref_res(body)
    
    refs = {}
    index = 0
    
    while index < len(decoded_body):
        length_hex = decoded_body[index:index + 4].decode("utf-8")
        index += 4
        
        if length_hex == "0000":
            continue
        
        length = int(length_hex, 16)
        if length == 0:
            break
        
        content = decoded_body[index:index + length - 4].decode("utf-8")
        index += length - 4
        
        if content.startswith("# service="):
            continue
        
        if "HEAD" in content or "refs/" in content:
            parts = content.split(" ")
            obj_id = parts[0]
            ref_name = parts[1].split("\0")[0].strip()
            refs[ref_name] = obj_id

    return refs

def save_pack_file(pack_file_res):
    packfile_data = pack_file_res.split(b"PACK", 1)[1]
    packfile_data = b"PACK" + packfile_data
    packfile_dir = f"{os.curdir}/packfile/"
    
    os.makedirs(packfile_dir, exist_ok=True)
    packfile_path = os.path.join(packfile_dir, "packfile.pack")
    with open(packfile_path, "wb") as file:
        file.write(packfile_data)
    
    print(f"Packfile saved to {packfile_path}")
    return packfile_path

def parse_object(packfile_data):
    first_byte = packfile_data[0]
    # print(f"First byte: {first_byte:08b}")
    obj_type = (first_byte >> 4) & 0b111
    obj_type_name = GIT_OBJECT_TYPES.get(str(obj_type), "UNKNOWN")
    # print(f"Object type: {obj_type_name} ({obj_type})")
    
    size = first_byte & 0b1111
    # print(f"Initial size: {size}")
    
    traverse_index = 1
    shift = 4
    while first_byte & 0b10000000:
        first_byte = packfile_data[traverse_index]
        # print(f"Next byte: {first_byte:08b}")
        size |= (first_byte & 0b01111111) << shift
        # print(f"Updated size: {size}")
        shift += 7
        traverse_index += 1
        
    return obj_type_name, size, packfile_data[traverse_index:]

def unpack_packfile(packfile_path):
    with open(packfile_path, "rb") as file:
        packfile_data = file.read()
    version = int.from_bytes(packfile_data[4:8])
    object_count = int.from_bytes(packfile_data[8:12])
    
    packfile_data = packfile_data[12:]
    print(packfile_data[20:])
    for i in range(object_count):
        obj_type, obj_size, packfile_data = parse_object(packfile_data)
        # print(f"Type: {obj_type}, Size: {obj_size}")
      

def clone_repo(git_url, dir):
    pack_file_res = fetch_pack_file(git_url)
    packfile_path = save_pack_file(pack_file_res)
    unpack_packfile(packfile_path)
    

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
