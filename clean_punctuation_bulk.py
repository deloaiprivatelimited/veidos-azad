import re
import json
from pathlib import Path
import shutil

# ==========================================
# CONFIG
# ==========================================

BASE_DIR = Path("class 8 part1")
CREATE_BACKUP = True

# ==========================================
# PUNCTUATION CLEANER
# ==========================================

def clean_punctuation(text: str) -> str:
    if not text:
        return text

    # Replace multiple dots with single dot
    text = re.sub(r"\.{2,}", ".", text)

    # Remove space before punctuation
    text = re.sub(r"\s+([.,:;!?])", r"\1", text)

    # Ensure single space after punctuation (except end)
    text = re.sub(r"([.,:;!?])([^\s])", r"\1 \2", text)

    # Fix multiple spaces
    text = re.sub(r"\s{2,}", " ", text)

    # Fix multiple newlines
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()

# ==========================================
# PROCESS FILE
# ==========================================

def process_file(path: Path):
    print(f"\n📄 Processing: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    modified = False

    for chunk in data.get("chunks", []):
        original = chunk.get("script", "")
        cleaned = clean_punctuation(original)

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
# MAIN
# ==========================================

def main():
    chunk_files = list(BASE_DIR.rglob("modules/chunks/*.json"))

    print(f"\n🔍 Found {len(chunk_files)} chunk files\n")

    for file in chunk_files:
        process_file(file)

    print("\n🎉 All files cleaned successfully.")

if __name__ == "__main__":
    main()