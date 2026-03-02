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
VALIDATION_PROMPT_PATH = os.path.join("promts", "master_data_validation_prompt.txt")
AUTO_FIX_PROMPT_PATH = os.path.join("promts", "master_data_autofix_prompt.txt")

MAX_WORKERS = 5
MAX_ATTEMPTS = 3

# Use environment variable (RECOMMENDED)
client = genai.Client(api_key='AIzaSyBxAK4R-IUkN0d2qN4C5Q2Z1m-wbmJsrGI')

# ============================================================
# LOAD PROMPTS
# ============================================================

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

validation_prompt = load_text(VALIDATION_PROMPT_PATH)
auto_fix_prompt = load_text(AUTO_FIX_PROMPT_PATH)

# ============================================================
# SCHEMA
# ============================================================

class LMSValidationReport(BaseModel):
    coverage_status: str
    subject_accuracy: str
    concept_integrity: str
    diagram_integrity: str
    structural_compliance: str
    critical_issues: List[str]
    major_issues: List[str]
    minor_issues: List[str]
    release_recommendation: str

# ============================================================
# VALIDATION CALL
# ============================================================

def run_validation(pdf_bytes, master_text):

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[{
            "role": "user",
            "parts": [
                {"text": validation_prompt},
                {"text": "----- SOURCE PDF -----"},
                {"inline_data": {
                    "mime_type": "application/pdf",
                    "data": pdf_bytes
                }},
                {"text": "----- LMS GENERATED CONTENT -----"},
                {"text": master_text}
            ]
        }],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": LMSValidationReport.model_json_schema(),
        },
    )

    return LMSValidationReport.model_validate_json(response.text)

# ============================================================
# AUTO FIX CALL
# ============================================================

def run_auto_fix(pdf_bytes, master_text, current_report, previous_report=None):

    parts = [
        {"text": auto_fix_prompt},
        {"text": "----- SOURCE PDF -----"},
        {"inline_data": {
            "mime_type": "application/pdf",
            "data": pdf_bytes
        }},
        {"text": "----- EXISTING MASTER DATA -----"},
        {"text": master_text},
        {"text": "----- CURRENT VALIDATION REPORT -----"},
        {"text": json.dumps(current_report, ensure_ascii=False)}
    ]

    if previous_report:
        parts.append({"text": "----- PREVIOUS VALIDATION REPORT -----"})
        parts.append({"text": json.dumps(previous_report, ensure_ascii=False)})

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[{
            "role": "user",
            "parts": parts
        }]
    )

    return response.text

# ============================================================
# CHAPTER PROCESSING (BLOCKING)
# ============================================================

def process_chapter(chapter_path):

    master_file = os.path.join(chapter_path, "master_data.txt")
    validation_file = os.path.join(chapter_path, "validation_report.json")

    if not os.path.exists(master_file):
        return

    # Load previous validation if exists
    previous_report = None
    if os.path.exists(validation_file):
        try:
            with open(validation_file, "r", encoding="utf-8") as f:
                previous_report = json.load(f)

            if previous_report.get("release_recommendation") == "READY_TO_GO":
                print(f"⏭ Skipping (Already READY): {chapter_path}")
                return

        except Exception:
            previous_report = None

    # Find PDF
    pdf_file = None
    for file in os.listdir(chapter_path):
        if file.endswith(".pdf"):
            pdf_file = os.path.join(chapter_path, file)
            break

    if not pdf_file:
        return

    print(f"🔍 Processing: {chapter_path}")

    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()

    with open(master_file, "r", encoding="utf-8") as f:
        master_text = f.read()

    attempt = 1

    while attempt <= MAX_ATTEMPTS:

        print(f"   🔁 Attempt {attempt}")

        # -------- VALIDATE --------
        report = run_validation(pdf_bytes, master_text)

        # Save validation report
        with open(validation_file, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

        if report.release_recommendation == "READY_TO_GO":
            print(f"   ✅ Ready → {chapter_path}")
            return

        # -------- AUTO FIX --------
        print(f"   ⚠ Not Ready → Auto Fixing")

        master_text = run_auto_fix(
            pdf_bytes,
            master_text,
            report.model_dump(),
            previous_report
        )

        # Overwrite master data
        with open(master_file, "w", encoding="utf-8") as f:
            f.write(master_text)

        previous_report = report.model_dump()
        attempt += 1

    # If still failing after max attempts
    print(f"   ❌ Failed after {MAX_ATTEMPTS} attempts → Deleting master_data.txt")
    os.remove(master_file)

# ============================================================
# ASYNC PARALLEL WRAPPER
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

    print("\n🚀 All chapters processed.")

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())