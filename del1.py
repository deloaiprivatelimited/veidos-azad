import shutil
from pathlib import Path

BASE_CLASS_PATH = Path(__file__).parent / "class 8 part1"

deleted_videos = 0
deleted_slides = 0

def delete_generated_content():
    global deleted_videos, deleted_slides

    if not BASE_CLASS_PATH.exists():
        print("❌ Base folder not found.")
        return

    # Loop through chapters
    for chapter in BASE_CLASS_PATH.iterdir():
        if not chapter.is_dir():
            continue

        print(f"\n📂 Checking {chapter.name}")

        # Delete MP4 files inside chapter root
        for file in chapter.glob("*.mp4"):
            print(f"🗑 Deleting video: {file.name}")
            file.unlink()
            deleted_videos += 1

        # Delete slides_* folders
        for folder in chapter.glob("slides_*"):
            if folder.is_dir():
                print(f"🗑 Deleting slides folder: {folder.name}")
                shutil.rmtree(folder)
                deleted_slides += 1

    print("\n✅ Cleanup Complete")
    print(f"🎬 Videos deleted: {deleted_videos}")
    print(f"🖼 Slide folders deleted: {deleted_slides}")

if __name__ == "__main__":
    delete_generated_content()