import os
import shutil

# Source folder
source_folder = "class 8 part1"

# Get all PDF files in sorted order
files = sorted([
    f for f in os.listdir(source_folder)
    if f.lower().endswith(".pdf")
])

for index, filename in enumerate(files, start=1):
    old_path = os.path.join(source_folder, filename)

    # New file and folder names
    new_filename = f"chapter{index}.pdf"
    new_folder = f"chapter{index}"
    new_folder_path = os.path.join(source_folder, new_folder)

    # Create chapter folder if it doesn't exist
    os.makedirs(new_folder_path, exist_ok=True)

    # Full new file path
    new_file_path = os.path.join(new_folder_path, new_filename)

    # Move and rename the file
    shutil.move(old_path, new_file_path)

    print(f"Moved: {filename} -> {new_folder}/{new_filename}")

print("\n✅ All files renamed and organized successfully!")