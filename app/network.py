import socket
import ssl
from urllib.parse import urlparse

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
        print(f"Length Hex: {length_hex}")
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
    print(f"{ref_res}")
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
    
    return packfile_response, head_sha