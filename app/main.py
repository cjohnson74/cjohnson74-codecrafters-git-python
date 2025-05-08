import sys
import os
import zlib


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
        print(f"blob: {blob}")
        folder = blob[:2]
        file = blob[2:]
        print(f"folder: {folder}, file: {file}")
        with open(f".git/objects/{folder}/{file}", "rb") as blob_file:
            contents = zlib.decompress(blob_file.read())
            print(f"contents: {contents}")
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
