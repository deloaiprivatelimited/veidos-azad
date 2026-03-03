import os

def count_mp4_files(base_path="."):
    total = 0

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(".mp4"):
                total += 1

    return total

if __name__ == "__main__":
    count = count_mp4_files()
    print(f"Total .mp4 files: {count}")