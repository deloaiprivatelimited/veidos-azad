import wave
from pathlib import Path
from datetime import datetime
import re

# ==============================
# CONFIG
# ==============================
BASE_DIR = Path("class 8 part1")
OUTPUT_FILE = "audio_statistics_report.txt"


# ==============================
# UTIL
# ==============================
def get_wav_duration(file_path: Path) -> float:
    with wave.open(str(file_path), 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def format_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def natural_sort_key(text):
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split('([0-9]+)', text)]


# ==============================
# MAIN
# ==============================
def generate_report():
    total_duration_all = 0
    total_modules = 0
    lines = []

    lines.append("=" * 70)
    lines.append("AUDIO / VIDEO LENGTH STATISTICS REPORT")
    lines.append(f"Generated on: {datetime.now()}")
    lines.append("=" * 70)

    chapters = sorted(
        [c for c in BASE_DIR.glob("chapter*") if c.is_dir()],
        key=lambda x: natural_sort_key(x.name)
    )

    for chapter in chapters:
        chapter_total = 0
        module_count = 0

        lines.append(f"\n{chapter.name.upper()}")
        lines.append("-" * 50)

        # Find all final_module.wav inside this chapter
        audio_files = list(chapter.rglob("final_module.wav"))

        # Sort by module number
        audio_files.sort(key=lambda x: natural_sort_key(str(x)))

        for audio_file in audio_files:
            duration = get_wav_duration(audio_file)

            # Extract module name (m1, m2 etc.)
            parts = audio_file.parts
            module_name = "UNKNOWN"
            for part in parts:
                if part.startswith("m") and part[1:].isdigit():
                    module_name = part
                    break

            lines.append(f"{module_name:<8} | {format_time(duration)}")

            chapter_total += duration
            total_duration_all += duration
            module_count += 1
            total_modules += 1

        lines.append("-" * 50)
        lines.append(f"Modules Count : {module_count}")
        lines.append(f"Chapter Total : {format_time(chapter_total)}")

    lines.append("\n" + "=" * 70)
    lines.append("OVERALL SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Total Modules (Videos): {total_modules}")
    lines.append(f"Total Duration        : {format_time(total_duration_all)}")
    lines.append("=" * 70)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_report()