import json
import vertexai
from vertexai.generative_models import GenerativeModel

# ==========================================
# CONFIG
# ==========================================

PROJECT_ID = "lively-aloe-411504"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-pro"

INPUT_MODULE_PATH = "class 8 part1\chapter1\modules\m1.json"
OUTPUT_PATH = "gemini_elite_output.txt"

# ==========================================
# INITIALIZE VERTEX AI
# ==========================================

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_NAME)

# ==========================================
# LOAD MODULE JSON
# ==========================================

with open(INPUT_MODULE_PATH, "r", encoding="utf-8") as f:
    module_data = json.load(f)

chapter_title = module_data["chapter_title"]
module_title = module_data["module_metadata"]["module_title"]
section_content = module_data["section_content"]

# ==========================================
# STRICT SYLLABUS-BOUND PROMPT
# ==========================================

elite_prompt = f"""
You are a senior academic content developer preparing instructional material strictly aligned to a prescribed syllabus for GPSTR aspirants.

Your task is to generate analytically rich instructional content for the following module.

IMPORTANT SYLLABUS CONSTRAINT:

- You must strictly use ONLY the information present in the provided content.
- Do NOT introduce new historical facts.
- Do NOT add additional examples not present in the text.
- Do NOT extend discussion beyond the given scope.
- Do NOT reference future chapters or topics.
- Do NOT speculate.
- Do NOT generalize beyond what is stated.

You may:
- Clarify concepts.
- Deepen explanation.
- Strengthen analytical distinctions.
- Improve logical flow.
- Expand reasoning using ONLY the provided material.

Chapter: {chapter_title}
Module: {module_title}

Provided Content:
{section_content}

Generate a cohesive, academically rigorous explanatory narrative strictly confined to the above content.
"""

# ==========================================
# GENERATE CONTENT
# ==========================================

response = model.generate_content(
    elite_prompt,
    generation_config={
        "temperature": 0.2,  # lower = safer, less scope drift
        "top_p": 0.9
    }
)

elite_output = response.text

# ==========================================
# SAVE OUTPUT
# ==========================================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(elite_output)

print("✅ Syllabus-bound elite content generated and saved to:", OUTPUT_PATH)