import os
import zlib
from objects import hash_object, write_tree, read_tree_object
from network import fetch_pack_file

GIT_OBJECT_TYPES = {
    "1": "COMMIT",
    "2": "TREE",
    "3": "BLOB",
    "4": "TAG",
    "6": "OFS_DELTA",
    "7": "REF_DELTA"
}

def get_extended_size(initial_size, packfile_data):
    size = initial_size
    index = 0
    shift = 0
    
    while True:
        byte = packfile_data[index]
        index += 1
        size |= (byte & 0b01111111) << shift
        if not (byte & 0b10000000):
            break
        shift += 7
    
    return size, packfile_data[index:]

def parse_object(packfile_data):
    first_byte = packfile_data[0]
    # print(f"First byte: {first_byte:08b}")
    obj_type = (first_byte >> 4) & 0b111
    obj_type_name = GIT_OBJECT_TYPES.get(str(obj_type), "UNKNOWN")
    
    initial_size = first_byte & 0b1111
    obj_size, packfile_data = get_extended_size(initial_size, packfile_data[1:])
    
    print(f"Object type: {obj_type_name} ({obj_type}), Size: {obj_size}")
    return obj_type_name, obj_size, packfile_data

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

def process_commit(obj_size, packfile_data):
    obj_data = packfile_data[:obj_size]
    # print(f"Raw Commit Object Data (hex): {obj_data.hex()}")
    try:
        obj_data_decoded = zlib.decompress(obj_data).decode("utf-8")
    except zlib.error as e:
        print(f"Decompression Error: {e}")
        raise ValueError("Failed to decompress commit object data")
    
    print(f"Commit Object Data: {obj_data_decoded}")
    
    commit_sha = hash_object(obj_data, obj_type="commit")
    
    return commit_sha

def process_tree(obj_size, packfile_data):
    obj_data = packfile_data[:obj_size]
    # print(f"Raw Tree Object Data (hex): {obj_data.hex()}")
    try:
        obj_data_decoded = zlib.decompress(obj_data).decode("utf-8")
    except zlib.error as e:
        print(f"Decompression Error: {e}")
        raise ValueError("Failed to decompress commit object data")
    
    print(f"Tree Object Data: {obj_data_decoded}")
    
    hash_object(obj_data, obj_type="tree")
    working_dir = os.getcwd()
    tree_sha = write_tree(working_dir)
    
    return tree_sha

def parse_copy_instruction(obj_data):
    instruction_byte = obj_data[0]
    obj_data = obj_data[1:]
    
    size = 0
    offset = 0
    
    shift = 0
    offset_bits = instruction_byte & 0b1111
    while offset_bits:
        if offset_bits & 0b1:
            offset |= obj_data[0] << shift
            obj_data[1:]
        shift += 8
        offset_bits >> 1
    
    shift = 0
    size_bits = (instruction_byte >> 4) & 0b111
    while size_bits:
        if size_bits & 0b1:
            size |= obj_data[0] << shift
            obj_data[0]
        shift += 8
        size_bits >> 1
    
    return offset, size, obj_data

def process_ref_deltas(ref_deltas):
    for (sha, obj_data) in ref_deltas:
        source_size, obj_data = get_extended_size(0, obj_data)
        target_size, obj_data = get_extended_size(0, obj_data)
        target_obj_data = b""
        
        with open(f".git/objects/{sha[:2]/sha[2:]}", "rb") as file:
            existing_obj_data = zlib.decompress(file.read())
            obj_type, data = existing_obj_data.split("\0", 1)
        
        while obj_data:
            instruction_byte = obj_data[0]
            if instruction_byte & 0b10000000:
                offset, size, obj_data = parse_copy_instruction(obj_data)
                target_obj_data += existing_obj_data[offset:offset+size]
            else:
                size = instruction_byte & 0b01111111
                target_obj_data += existing_obj_data[1:size]
                
        return hash_object(target_obj_data, obj_type)

def unpack_packfile(packfile_path):
    with open(packfile_path, "rb") as file:
        packfile_data = file.read()
    version = int.from_bytes(packfile_data[4:8], byteorder="big")
    object_count = int.from_bytes(packfile_data[8:12], byteorder="big")
    print(f"Packfile Version: {version}, Object Count: {object_count}")
    packfile_data = packfile_data[12:]

    ref_deltas = []
    for i in range(object_count):
        obj_type, obj_size, packfile_data = parse_object(packfile_data)
        
        decompressor = zlib.decompressobj()
        if obj_type in ["COMMIT", "TREE", "BLOB"]:
            print(f"Object Type: {obj_type}")
            obj_data = decompressor.decompress(packfile_data, obj_size)
            decompressor.flush()
            hash_object(obj_data, obj_type)
        else:
            delta_sha, packfile_data = packfile_data[:20], packfile_data[20:]
            obj_data = decompressor.decompress(packfile_data, obj_size)
            decompressor.flush()
            ref_deltas.append((delta_sha.hex(), obj_data))
        
        packfile_data = decompressor.unused_data
        
        process_ref_deltas(ref_deltas)
        
def checkout_tree(tree_sha, dir):
    entries = read_tree_object(tree_sha)
    for entry in entries:
        print(f"{entry}")
    
def clone_repo(git_url, dir):
    pack_file_res, head_sha = fetch_pack_file(git_url)
    packfile_path = save_pack_file(pack_file_res)
    unpack_packfile(packfile_path)
    
    tree_sha = read_tree_object(head_sha)[0]['sha']
    checkout_tree(tree_sha, dir)
    