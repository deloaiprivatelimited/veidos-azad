import os
import json
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor

from google import genai
from pydantic import BaseModel

# ============================================================
# CONFIG
# ============================================================

ROOT_FOLDER = "class 8 part1"
PROMPT_PATH = os.path.join("promts", "generate_modules.txt")
MAX_WORKERS = 5

# Use environment variable (recommended)
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

# ============================================================
# SCHEMA
# ============================================================

class Module(BaseModel):
    module_id: str
    module_title: str
    merged_source_sections: List[str]
    concept_scope_summary: str
    cognitive_focus: str
    estimated_duration_minutes: str
    reason_for_grouping: str

class ChapterModules(BaseModel):
    chapter_title: str
    chapter_objective: str
    total_modules: int
    modules: List[Module]

# ============================================================
# LOAD PROMPT
# ============================================================

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

module_prompt = load_prompt(PROMPT_PATH)

# ============================================================
# GENERATE MODULE STRUCTURE
# ============================================================

def generate_modules_blocking(master_data_text):

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[{
            "role": "user",
            "parts": [
                {"text": module_prompt},
                {"text": "----- FULL CHAPTER MASTER DATA -----"},
                {"text": master_data_text}
            ]
        }],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": ChapterModules.model_json_schema(),
        },
    )

    return ChapterModules.model_validate_json(response.text)

# ============================================================
# SECTION EXTRACTION LOGIC
# ============================================================

def extract_sections(master_text, section_labels):
    """
    Extract only requested conceptual sections including full block
    until next conceptual header.
    """

    extracted = []
    lines = master_text.splitlines()

    capture = False
    current_section = None

    for line in lines:

        stripped = line.strip()

        if stripped.startswith("[ಮೂಲ_ಅವಧಾರಣೆ_"):
            label = stripped.replace("[", "").replace("]", "")
            current_section = label
            capture = label in section_labels

        if capture:
            extracted.append(line)

    return "\n".join(extracted).strip()

# ============================================================
# PROCESS SINGLE CHAPTER
# ============================================================

def process_chapter(chapter_path):

    master_file = os.path.join(chapter_path, "master_data.txt")
    if not os.path.exists(master_file):
        return

    modules_dir = os.path.join(chapter_path, "modules")

    # Skip if modules already exist
    if os.path.exists(modules_dir) and os.listdir(modules_dir):
        print(f"⏭ Skipping (Modules exist): {chapter_path}")
        return

    print(f"📘 Generating modules: {chapter_path}")

    with open(master_file, "r", encoding="utf-8") as f:
        master_data = f.read()

    try:
        modules_data = generate_modules_blocking(master_data)

        os.makedirs(modules_dir, exist_ok=True)

        for module in modules_data.modules:

            relevant_content = extract_sections(
                master_data,
                module.merged_source_sections
            )

            module_payload = {
                "chapter_title": modules_data.chapter_title,
                "chapter_objective": modules_data.chapter_objective,
                "total_modules": modules_data.total_modules,
                "module_metadata": module.model_dump(),
                "section_content": relevant_content
            }

            module_file = os.path.join(
                modules_dir,
                f"{module.module_id}.json"
            )

            with open(module_file, "w", encoding="utf-8") as f:
                json.dump(module_payload, f, indent=2, ensure_ascii=False)

        print(f"✅ {modules_data.total_modules} modules saved in /modules")

    except Exception as e:
        print(f"❌ Module generation failed: {chapter_path} → {e}")

# ============================================================
# ASYNC WRAPPER
# ============================================================

async def main():

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        tasks = []

        for chapter in os.listdir(ROOT_FOLDER):
            chapter_path = os.path.join(ROOT_FOLDER, chapter)

            if os.path.isdir(chapter_path):
                task = loop.run_in_executor(
                    executor,
                    process_chapter,
                    chapter_path
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

    print("\n🚀 All module generations completed.")

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())