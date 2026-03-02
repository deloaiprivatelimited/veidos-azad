import os
import json
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor

from google import genai
from pydantic import BaseModel

# -----------------------------
# CONFIG
# -----------------------------

ROOT_FOLDER = "class 8 part1"
PROMPT_PATH = os.path.join("promts", "master_data_validation_prompt.txt")
MAX_WORKERS = 5   # Adjust based on quota

client = genai.Client(api_key='AIzaSyBxAK4R-IUkN0d2qN4C5Q2Z1m-wbmJsrGI')


# -----------------------------
# LOAD PROMPT
# -----------------------------

def load_validation_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

validation_prompt = load_validation_prompt(PROMPT_PATH)


# -----------------------------
# SCHEMA
# -----------------------------

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


# -----------------------------
# SINGLE VALIDATION (Blocking)
# -----------------------------

def validate_chapter_blocking(chapter_path):

    validation_file = os.path.join(chapter_path, "validation_report.json")
    master_file = os.path.join(chapter_path, "master_data.txt")

    if not os.path.exists(master_file):
        return

    # -------------------------------------------------
    # CHECK EXISTING VALIDATION STATUS
    # -------------------------------------------------

    if os.path.exists(validation_file):
        try:
            with open(validation_file, "r", encoding="utf-8") as f:
                existing_report = json.load(f)

            if existing_report.get("release_recommendation") == "READY_TO_GO" :
                print(f"⏭ Skipping (Already READY): {chapter_path}")
                return
            else:
                print(f"🔁 Re-validating (Not READY): {chapter_path}")

        except Exception:
            print(f"⚠ Corrupted validation file → Re-validating: {chapter_path}")

    # -------------------------------------------------
    # FIND PDF
    # -------------------------------------------------

    pdf_file = None
    for file in os.listdir(chapter_path):
        if file.endswith(".pdf"):
            pdf_file = os.path.join(chapter_path, file)
            break

    if not pdf_file:
        return

    print(f"🔍 Validating: {chapter_path}")

    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()

    with open(master_file, "r", encoding="utf-8") as f:
        master_text = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[{
            "role": "user",
            "parts": [
                {"text": validation_prompt},
                {"text": "----- ಮೂಲ ಪಠ್ಯಪುಸ್ತಕ ವಿಷಯ -----"},
                {"inline_data": {
                    "mime_type": "application/pdf",
                    "data": pdf_bytes
                }},
                {"text": "----- LMS Generated Reference Content -----"},
                {"text": master_text}
            ]
        }],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": LMSValidationReport.model_json_schema(),
        },
    )

    report = LMSValidationReport.model_validate_json(response.text)

    # Save new validation report
    with open(validation_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

    # -------------------------------------------------
    # GATE DECISION
    # -------------------------------------------------

    if report.release_recommendation != "READY_TO_GO" and report.release_recommendation != "NEEDS_REVISION":
        os.remove(master_file)
        print(f"❌ Deleted master_data.txt → {chapter_path}")
    else:
        print(f"✅ Ready → {chapter_path}")
# -----------------------------
# ASYNC WRAPPER
# -----------------------------

async def main():

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = []

        for chapter in os.listdir(ROOT_FOLDER):
            chapter_path = os.path.join(ROOT_FOLDER, chapter)

            if os.path.isdir(chapter_path):
                task = loop.run_in_executor(
                    executor,
                    validate_chapter_blocking,
                    chapter_path
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

    print("\n🚀 All validations completed.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    asyncio.run(main())