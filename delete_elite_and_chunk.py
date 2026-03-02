import os
import shutil

ROOT_DIR = "."  # Project root

deleted_files = 0
deleted_folders = 0

for root, dirs, files in os.walk(ROOT_DIR, topdown=False):

    # Delete _elite.txt files
    for file in files:
        if file.endswith("_elite.txt"):
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                deleted_files += 1
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")

    # Delete chunks folders
    for dir_name in dirs:
        if dir_name == "chunks":
            folder_path = os.path.join(root, dir_name)
            try:
                shutil.rmtree(folder_path)
                deleted_folders += 1
                print(f"Deleted folder: {folder_path}")
            except Exception as e:
                print(f"Failed to delete folder {folder_path}: {e}")

print("\nCleanup Complete")
print(f"Total _elite.txt files deleted: {deleted_files}")
print(f"Total chunks folders deleted: {deleted_folders}")