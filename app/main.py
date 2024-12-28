from argparse import ArgumentParser
import os


def main():
    parser = ArgumentParser()
    parser.add_argument("command", help="The command to run")
    args = parser.parse_args()
    command = args.command
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
