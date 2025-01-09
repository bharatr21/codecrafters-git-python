from argparse import ArgumentParser
import sys
import os
import zlib

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
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
