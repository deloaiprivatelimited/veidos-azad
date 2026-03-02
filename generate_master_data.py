import os
import asyncio
import vertexai
from concurrent.futures import ThreadPoolExecutor
from vertexai.generative_models import GenerativeModel, Part

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_ID = "lively-aloe-411504"
LOCATION = "us-central1"
ROOT_FOLDER = "class 8 part1"
PROMPT_PATH = "promts/master_data_prompt.txt"
MAX_WORKERS = 5   # Adjust based on quota

# -----------------------------
# INIT VERTEX
# -----------------------------
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-2.5-pro")

# -----------------------------
# LOAD PROMPT
# -----------------------------
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    master_prompt = f.read()

# -----------------------------
# PROCESS SINGLE CHAPTER
# -----------------------------
def process_chapter(chapter_path):
    output_path = os.path.join(chapter_path, "master_data.txt")

    # ✅ Skip if already processed
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"Skipping (already processed): {chapter_path}")
        return
    pdf_file = None
    for file in os.listdir(chapter_path):
        if file.lower().endswith(".pdf"):
            pdf_file = os.path.join(chapter_path, file)
            break

    if not pdf_file:
        print(f"No PDF in {chapter_path}")
        return

    print(f"Processing {pdf_file}")

    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()

    pdf_part = Part.from_data(
        data=pdf_bytes,
        mime_type="application/pdf"
    )

    response = model.generate_content([
        pdf_part,
        master_prompt
    ])

    output_path = os.path.join(chapter_path, "master_data.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Saved master_data.txt in {chapter_path}")

# -----------------------------
# ASYNC WRAPPER
# -----------------------------
async def main():
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = []

        for chapter_folder in os.listdir(ROOT_FOLDER):
            chapter_path = os.path.join(ROOT_FOLDER, chapter_folder)

            if os.path.isdir(chapter_path):
                task = loop.run_in_executor(
                    executor,
                    process_chapter,
                    chapter_path
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

    print("All chapters processed.")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    asyncio.run(main())