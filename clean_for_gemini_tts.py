import re
import json
from pathlib import Path
import shutil

# ==========================================
# CONFIG
# ==========================================

BASE_DIR = Path("class 8 part1")
CREATE_BACKUP = True   # Safety first

# ==========================================
# CLEAN SSML FUNCTION
# ==========================================

def clean_ssml(text: str) -> str:
    if not text:
        return text

    # Remove <speak> tags
    text = re.sub(r"</?speak>", "", text)

    # Remove <mark .../>
    text = re.sub(r"<mark[^>]*\/>", "", text)

    # Replace <break .../> with period
    text = re.sub(r"<break[^>]*\/>", ". ", text)

    # Remove any remaining XML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Fix spacing
    text = re.sub(r"\s+", " ", text).strip()

    return text

# ==========================================
# PROCESS SINGLE FILE
# ==========================================

def process_file(path: Path):

    print(f"\n📄 Processing: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    modified = False

    for chunk in data.get("chunks", []):
        original = chunk.get("script", "")
        cleaned = clean_ssml(original)

        if cleaned != original:
            chunk["script"] = cleaned
            modified = True

    if not modified:
        print("⏭ Already clean")
        return

    # Backup
    if CREATE_BACKUP:
        backup_path = path.with_suffix(".backup.json")
        shutil.copy(path, backup_path)
        print(f"🛟 Backup created: {backup_path}")

    # Save cleaned file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Cleaned and saved")

# ==========================================
# MAIN BULK RUN
# ==========================================

def main():

    chunk_files = list(BASE_DIR.rglob("modules/chunks/*.json"))

    print(f"\n🔍 Found {len(chunk_files)} chunk files\n")

    for file in chunk_files:
        process_file(file)

    print("\n🎉 All chunk files processed successfully.")

if __name__ == "__main__":
    main()