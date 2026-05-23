import subprocess
import sys
import re

def get_git_files():
    try:
        output = subprocess.check_output(["git", "ls-files"], text=True)
        return output.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to list git files: {e}")
        return []

def validate_paths(files):
    invalid_files = []

    # Pattern for Windows absolute paths (C:/...)
    abs_win_pattern = re.compile(r"^[a-zA-Z]:/")
    # Pattern for colons in filenames (illegal on Windows Actions)
    colon_pattern = re.compile(r":")

    # Forbidden runtime directories
    forbidden_dirs = [
        "data/",
        "storage/runtime/",
        "storage/memory/",
        "storage/cognition/",
        "storage/governance/",
        "storage/federation/",
        "storage/sandbox/",
        "storage/providers/",
        "storage/logs/",
        "storage/snapshots/",
        "storage/temp/",
        "runtime/",
        "logs/"
    ]

    for f in files:
        # Check for absolute paths or colons
        if abs_win_pattern.match(f) or colon_pattern.search(f):
            invalid_files.append(f"INVALID_PATH: {f}")
            continue

        # Check for forbidden runtime data
        for d in forbidden_dirs:
            if f.startswith(d):
                invalid_files.append(f"FORBIDDEN_DIR: {f}")
                break

    return invalid_files

def main():
    print("Validating repository storage architecture...")
    files = get_git_files()
    if not files:
        print("No files found in git index.")
        sys.exit(0)

    invalid = validate_paths(files)

    if invalid:
        print("\nCRITICAL ARCHITECTURAL ERROR DETECTED")
        print("====================================")
        print("The following files are incorrectly tracked in the repository:")
        for error in invalid:
            print(f" - {error}")
        print("\nREASON: Runtime data or absolute paths must never be tracked in Git.")
        print("FIX: Run 'git rm --cached <path>' and ensure your storage logic uses RuntimeStorageManager.")
        sys.exit(1)
    else:
        print("SUCCESS: No invalid storage paths detected in git index.")
        sys.exit(0)

if __name__ == "__main__":
    main()
