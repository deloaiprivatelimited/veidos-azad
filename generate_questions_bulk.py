import os
from google import genai
from pydantic import BaseModel
from typing import List

BASE_DIR = "class 8 part1"
MODEL_NAME = "gemini-3-flash-preview"

class MCQ(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: str

class QuestionSet(BaseModel):
    chapter_name: str
    mcqs: List[MCQ]
    short_questions: List[str]
    long_questions: List[str]

QUESTION_PROMPT = """
You are an expert Karnataka GPST / HSTR Social Science question paper setter.

Generate a comprehensive CHAPTER-LEVEL QUESTION BANK.

This must fully and proportionally cover all concepts, subtopics,
timelines, definitions, classifications, comparisons, Karnataka-related
references, and cause-effect relationships from the chapter master data.

-----------------------------------
MCQs
-----------------------------------
- Include a strong mix of:
  • Factual
  • Conceptual
  • Chronology/order-based
  • Cause-effect
  • Comparison-based
  • Scenario/application-based
  • Trap-based conceptual clarity questions
- Avoid direct textbook-line copying.
- Ensure coverage of every major section.
- Provide 4 options.
- Provide answer_index (0-based).
- Provide explanation ONLY for MCQs.

-----------------------------------
Short Answer Questions
-----------------------------------
- 2–3 mark level.
- Include definition, distinction, reasoning, and brief analytical types.
- Include comparison and cause-based questions where relevant.
- Do NOT provide answers.

-----------------------------------
Long Answer Questions
-----------------------------------
- Analytical 5-mark level.
- Include classification, comparison, cause-effect, and evaluation type questions.
- Encourage structured and critical thinking.
- Do NOT provide answers.

-----------------------------------
QUALITY REQUIREMENTS
-----------------------------------
- Cover all major concepts proportionally.
- Maintain competitive GPST/HSTR standard.
- Avoid repetition.
- Ensure conceptual depth.
- Include applied and analytical framing.
- Balance difficulty naturally (basic to advanced).

-----------------------------------
OUTPUT RULES
-----------------------------------
- Follow the given JSON schema strictly.
- Return valid JSON only.
- Do not add commentary outside JSON.

-----------------------------------
CHAPTER MASTER DATA:
-----------------------------------
{chapter_content}
"""

def generate_questions():
    client = genai.Client()

    for chapter in os.listdir(BASE_DIR):
        chapter_path = os.path.join(BASE_DIR, chapter)

        if not os.path.isdir(chapter_path):
            continue

        master_file = os.path.join(chapter_path, "master_data.txt")

        if not os.path.exists(master_file):
            continue
        output_path = os.path.join(
            chapter_path,
            "chapter_questions.json"
        )

        # ✅ Skip if already generated
        if os.path.exists(output_path):
            print(f"Skipping {chapter} (already generated)")
            continue

        print(f"Generating questions for {chapter}...")

        with open(master_file, "r", encoding="utf-8") as f:
            chapter_content = f.read()

        prompt = QUESTION_PROMPT.format(
            chapter_content=chapter_content
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": QuestionSet.model_json_schema(),
                "temperature": 0.4,
            },
        )

        output_path = os.path.join(
            chapter_path,
            "chapter_questions.json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"Saved: {output_path}")

if __name__ == "__main__":
    generate_questions()