[![progress-banner](https://backend.codecrafters.io/progress/git/fb24059f-19b7-44b7-b8f1-ac5e92a79827)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

# Build Your Own Git - Progress and Learnings

This project is part of the ["Build Your Own Git" Challenge](https://codecrafters.io/challenges/git). The goal is to build a small Git implementation that's capable of initializing a repository, creating commits and cloning a public repository.
Along the way I'll learned about the `.git` directory, Git objects (blobs,
commits, trees etc.), Git's transfer protocols and more.

## Features Implemented

### 1. Repository Initialization (`init`)
- **What it does**: Creates a `.git` directory with the necessary subdirectories (`objects`, `refs`) and a `HEAD` file pointing to the default branch (`refs/heads/main`).
- **Key Learnings**:
  - Git repositories are initialized with a specific directory structure.
  - The `HEAD` file determines the current branch.

### 2. Reading Blob Objects (`cat-file`)
- **What it does**: Reads and decompresses a blob object stored in `.git/objects` and prints its content.
- **Key Learnings**:
  - Git stores objects in a compressed format using zlib.
  - Objects are identified by their SHA-1 hash and stored in a directory structure based on the first two characters of the hash.

### 3. Hashing and Storing Objects (`hash-object`)
- **What it does**: Computes the SHA-1 hash of a file's content, creates a blob object, and stores it in `.git/objects`.
- **Key Learnings**:
  - Git objects include a header (e.g., `blob <size>\0`) followed by the content.
  - The SHA-1 hash is computed from the header and content combined.
  - Objects are stored in a compressed format.

### 4. Reading Tree Objects (`ls-tree`)
- **What it does**: Reads a tree object and lists its entries (files and subdirectories).
- **Key Learnings**:
  - Tree objects store file metadata (mode, name) and references to blob or tree objects.
  - Entries are stored in a binary format with null-terminated names and raw SHA-1 hashes.

### 5. Writing Tree Objects (`write-tree`)
- **What it does**: Recursively traverses the working directory, hashes files as blobs, and creates a tree object representing the directory structure.
- **Key Learnings**:
  - Tree objects are hierarchical and can reference other tree objects.
  - Directory traversal and sorting are essential for consistent tree creation.

### 6. Writing Commit Objects (`commit-tree`)
- **What it does**: Creates a commit object referencing a tree object and a parent commit, with metadata (author, committer, timestamp) and a commit message.
- **Key Learnings**:
  - Commit objects reference a tree object and optionally a parent commit.
  - Metadata includes the author's name, email, and timestamp.
  - Commit messages are stored as part of the commit object.

### 7. Fetching Remote Repository Information (`fetch_head_sha`)
- **What it does**: Connects to a remote Git repository over HTTPS, retrieves the `HEAD` SHA-1 hash, and parses the response.
- **Key Learnings**:
  - Git uses the `info/refs` endpoint to retrieve references from a remote repository.
  - HTTPS requests can be made using Python's `ssl` and `socket` modules.
  - Parsing the response involves understanding Git's protocol.

### 8. Cloning a Repository (`clone`)
- **What it does**: Fetches the `HEAD` SHA-1 hash from a remote repository and prepares for cloning.
- **Key Learnings**:
  - Cloning involves fetching objects and references from a remote repository.
  - The `HEAD` reference determines the default branch.

---

## Git pkt-line Protocol

### Overview
Git uses the **pkt-line protocol** for communication between clients and servers during operations like fetching, pushing, and cloning. This protocol is a simple way to send and receive data over the wire, ensuring that both sides can parse the data efficiently.

### How pkt-line Works
- Each line of data is prefixed with a 4-byte hexadecimal length field.
- The length field includes the size of the data and the 4 bytes of the length field itself.
- A special "flush packet" (`0000`) is used to indicate the end of a sequence of pkt-lines.

### Example
A pkt-line containing the string `hello\n` would look like this:
```
0009hello\n
```
- `0009`: The total length of the line (4 bytes for the length + 5 bytes for `hello\n`).
- `hello\n`: The actual data.

### Use in Git
- **Fetching References**: When fetching references from a remote repository, the server responds with pkt-lines containing the refs and their corresponding SHA-1 hashes.
- **Capabilities Advertisement**: The server advertises its capabilities (e.g., `multi_ack`, `thin-pack`) using pkt-lines.
- **End of Communication**: A flush packet (`0000`) is sent to signal the end of a sequence.

### Key Learnings
- The pkt-line protocol is lightweight and efficient, making it ideal for Git's needs.
- Understanding pkt-line is essential for implementing features like fetching and pushing in a custom Git client.
- Parsing pkt-lines involves reading the length prefix, extracting the data, and handling flush packets appropriately.

---

## Challenges Faced
- **Understanding Git's Object Model**: Learning how Git stores blobs, trees, and commits was crucial for implementing features like `hash-object`, `write-tree`, and `commit-tree`.
- **Parsing Binary Data**: Tree objects and Git's protocol responses required careful handling of binary data.
- **Networking with Sockets**: Fetching remote repository information involved working with low-level socket programming and HTTPS.
- **Pkt-line Parsing**: Implementing pkt-line parsing required understanding its structure and handling edge cases like flush packets.

## Tools and Technologies Used
- **Python**: The entire implementation is written in Python, leveraging its standard library for file I/O, hashing, compression, and networking.
- **zlib**: Used for compressing and decompressing Git objects.
- **hashlib**: Used for computing SHA-1 hashes.
- **socket**: Used for making network connections to remote Git repositories.
- **ssl**: Used for secure HTTPS communication.

## Next Steps
- **Handling Multiple References**: Support fetching and storing multiple branches and tags.
- **Improving Error Handling**: Add robust error handling for edge cases, such as missing files or network failures.
- **Testing**: Write unit tests for each feature to ensure correctness and reliability.

## Key Takeaways
- Git's simplicity lies in its use of a few core object types (blob, tree, commit) and their relationships.
- Networking and protocol handling are integral to Git's distributed nature.
- The pkt-line protocol is a foundational part of Git's wire communication.
- Building a Git implementation from scratch provides deep insights into its design and functionality.

This project has been a rewarding journey into the internals of Git, and I look forward to implementing more advanced features in the future!