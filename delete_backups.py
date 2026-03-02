from pathlib import Path

BASE_DIR = Path("class 8 part1")

def main():
    backup_files = list(BASE_DIR.rglob("*.backup.json")) + \
                   list(BASE_DIR.rglob("*.markdown_backup.json"))

    print(f"Found {len(backup_files)} backup files\n")

    for file in backup_files:
        print("Deleting:", file)
        file.unlink()

    print("\nAll backup files deleted.")

if __name__ == "__main__":
    main()