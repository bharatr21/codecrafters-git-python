from argparse import ArgumentParser
import sys
import os
from pathlib import Path
import zlib
import hashlib
import stat
import time

def handle_cat_file(args):
    print(read_file(args.sha), end="")

def read_file(sha):
    with open(f".git/objects/{sha[:2]}/{sha[2:]}", "rb") as f:
        raw = zlib.decompress(f.read())
        start = raw.find(b" ")
        format = raw[:start].decode()
        content_start = raw.find(b"\x00")
        file_size = int(raw[start:content_start].decode())
        if file_size != len(raw[content_start + 1:]):
            raise Exception(f"Malformed object {sha}: File size mismatch")
        return raw[content_start + 1:].decode()

def create_object(file, binary=False, format="blob"):
    mode = "rb" if binary else "r"
    with open(file, mode) as f:
        content = f.read()
    byte_content = content.encode("utf-8") if not binary else content
    full_content = f"{format} {len(content)}\x00".encode("utf-8") + byte_content
    sha = hashlib.sha1(full_content).hexdigest()
    path = f".git/objects/{sha[:2]}/{sha[2:]}"
    if os.path.exists(path):
        return sha
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(zlib.compress(full_content))
    return sha

def write_object(parent: Path, type: str, content: bytes) -> str:
    content = type.encode() + b" " + f"{len(content)}\0".encode() + content
    hash = hashlib.sha1(content, usedforsecurity=False).hexdigest()
    compressed_content = zlib.compress(content)
    pre = hash[:2]
    post = hash[2:]
    p = parent / ".git" / "objects" / pre / post
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(compressed_content)
    return hash

def enumerate_tree(hash):
    dirs = []
    with open(f".git/objects/{hash[:2]}/{hash[2:]}", "rb") as f:
        raw = zlib.decompress(f.read())
        binary_data = raw.split(b"\x00", maxsplit=1)[-1]
        while binary_data:
            binary_list = binary_data.split(b"\x00", maxsplit=1)
            if len(binary_list) == 1:
                break
            mode, binary_data = binary_list
            name = mode.split()[-1]
            binary_data = binary_data[len(name) + 1:]
            dirs.append(name.decode())
    return dirs

def get_git_mode(path):
    if os.path.isfile(path):
        mode = os.stat(path).st_mode
        if stat.S_ISREG(mode): # Regular file
            return "100644"
        elif stat.S_ISDIR(mode): # Directory
            return "40000"
        elif stat.S_ISLNK(mode): # Symbolic link
            return "120000"
        elif stat.S_ISX(mode): # Executable
            return "100755"

def write_tree(path="./"):
    if os.path.isfile(path):
        return create_object(path, binary=True, format="blob")
    contents = sorted(
        os.listdir(path),
        key=lambda x: x if os.path.isfile(x) else f"{x}/"
    )
    s = b""
    for item in contents:
        if item == ".git":
            continue
        full_path = os.path.join(path, item)
        file_mode = "100644" if os.path.isfile(full_path) else "40000"
        s += f"{file_mode} {item}\0".encode()
        sha1 = int.to_bytes(int(write_tree(full_path), base=16), length=20, byteorder="big")
        s += sha1
    s = f"tree {len(s)}\0".encode() + s
    sha = hashlib.sha1(s).hexdigest()
    path = f".git/objects/{sha[:2]}/{sha[2:]}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(zlib.compress(s))
    return sha

def create_commit(tree_sha, message, parent_sha, author="Test Author <test@example.com>", committer="Test Author <test@example.com>"):
    content = f"tree {tree_sha}\n".encode("utf-8")
    if parent_sha:
        content += f"parent {parent_sha}\n".encode("utf-8")

    timestamp = "1739308850 -0500"
    content += f"author {author} {timestamp}\n".encode("utf-8")
    content += f"committer {committer} {timestamp}\n\n".encode("utf-8")
    content += message.encode("utf-8") + b"\n"

    header = f"commit {len(content)}\0".encode("utf-8")
    commit_object = header + content
    blob_sha = hashlib.sha1(commit_object, usedforsecurity=False).hexdigest()
    compressed_blob = zlib.compress(commit_object)
    path = f".git/objects/{blob_sha[:2]}/{blob_sha[2:]}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(compressed_blob)

    return blob_sha

def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file" and sys.argv[2] == "-p":
        print(read_file(sys.argv[3]), end="")
    elif command == "hash-object" and sys.argv[2] == "-w":
        print(create_object(sys.argv[3], binary=False))
    elif command == "ls-tree" and sys.argv[2] == "--name-only":
        hash = sys.argv[3]
        dirs = enumerate_tree(hash)
        print("\n".join(dirs))
    elif command == "write-tree":
        hash = write_tree("./")
        print(hash, end="")
    elif command == "commit-tree":
        tree_sha, _, commit_sha, _, message = sys.argv[2:]
        author = "Bharat <13381361+bharatr21@users.noreply.github.com>"
        committer = "Bharat <13381361+bharatr21@users.noreply.github.com>"
        commit_hash = create_commit(tree_sha, message, commit_sha, author, committer)
        print(commit_hash)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
