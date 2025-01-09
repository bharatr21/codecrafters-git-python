from argparse import ArgumentParser
import sys
import os
import zlib
import hashlib

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

def create_object(content, format="blob"):
    full_content = f"{format} {len(content)}\x00".encode() + content.encode()
    sha = hashlib.sha1(full_content).hexdigest()
    path = f".git/objects/{sha[:2]}/{sha[2:]}"
    if os.path.exists(path):
        return sha
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(zlib.compress(full_content))
    return sha

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
        with open(sys.argv[3], "r") as f:
            content = f.read()
        print(create_object(content))
    elif command == "ls-tree" and sys.argv[2] == "--name-only":
        hash = sys.argv[3]
        dirs = enumerate_tree(hash)
        print("\n".join(dirs))
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
