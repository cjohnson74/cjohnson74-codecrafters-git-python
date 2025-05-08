import sys
import os
import zlib
import hashlib


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
        folder = blob[:2]
        file = blob[2:]
        with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
            contents = zlib.decompress(blob_file.read()).decode("utf-8")
            type = contents.split(" ")[0]
            content = contents.split("\0")[1]
            print(content, end="")
    elif command == "hash-object":
        file = sys.argv[sys.argv.index("-w") + 1]
        with open(file) as file:
            data = file.read()
            blob_object = f"blob {len(data)}\0{data}"
            sha = hashlib.sha1(blob_object.encode("utf-8")).hexdigest()
            file_path = f".git/objects/{sha[:2]}/{sha[2:]}"
            os.makedirs(os.path.dirname(file_path))
            with open(file_path) as file:
                file.write(zlib.compress(blob_object))
            print(sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
