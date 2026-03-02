import os
import json
from typing import List, Literal
from openai import OpenAI
from pydantic import BaseModel, Field

# ============================================================
# CONFIG
# ============================================================

ELITE_TEXT_PATH = "gemini_elite_output.txt"
MODULE_JSON_PATH = r"class 8 part1\chapter1\modules\m1.json"
PROMPT_PATH = os.path.join("promts", "generate_chunks_strict.txt")
OUTPUT_JSON_PATH = "structured_chunks_output.json"

MODEL_NAME = "gpt-4.1"   # or "gpt-4.1"
TEMPERATURE = 0.2                 # Low randomness for compiler behavior

client = OpenAI(api_key="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")

# ============================================================
# SCHEMA DEFINITIONS
# ============================================================

class Animation(BaseModel):
    pause_after: float


class Visual(BaseModel):
    type: Literal["placeholder", "none"]
    alt_text: str
    detailed_description: str
    future_asset_id: str


class Display(BaseModel):
    title: str
    markdown: str
    equations: List[str]


class Chunk(BaseModel):
    chunk_id: str
    order: int
    chunk_type: Literal[
        "intro",
        "definition",
        "concept_explanation",
        "event_analysis",
        "structure_explanation",
        "map_analysis",
        "timeline_analysis",
        "cause_effect",
        "exam_tip",
        "pedagogy_note",
        "recap"
    ]
    script: str
    display: Display
    visual: Visual
    layout: Literal["left_text_right_visual", "left_text_only"]
    animation: Animation


class ModuleChunks(BaseModel):
    chapter_title: str
    module_id: str
    module_title: str
    target_exam: Literal["GPSTR"]
    chunks: List[Chunk] = Field(min_items=1, max_items=25)

# ============================================================
# LOAD FILES
# ============================================================

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

elite_text = load_text(ELITE_TEXT_PATH)
structuring_prompt_template = load_text(PROMPT_PATH)

with open(MODULE_JSON_PATH, "r", encoding="utf-8") as f:
    module_data = json.load(f)

chapter_title = module_data["chapter_title"]
module_id = module_data["module_metadata"]["module_id"]
module_title = module_data["module_metadata"]["module_title"]

# ============================================================
# BUILD FINAL PROMPT
# ============================================================

final_prompt = f"""
{structuring_prompt_template}

────────────────────────
MODULE CONTEXT
────────────────────────

Chapter Title: {chapter_title}
Module ID: {module_id}
Module Title: {module_title}

────────────────────────
ELITE SCRIPT (SOURCE MATERIAL)
────────────────────────

{elite_text}
"""

# ============================================================
# CALL OPENAI STRUCTURED OUTPUT
# ============================================================

response = client.responses.parse(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    input=[
        {
            "role": "system",
            "content": "You are a formatting engine. Do not modify content. Return strictly valid JSON matching the provided schema."
        },
        {
            "role": "user",
            "content": final_prompt
        }
    ],
    text_format=ModuleChunks,
)

structured_output = response.output_parsed

# ============================================================
# SAVE OUTPUT
# ============================================================

with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(structured_output.model_dump(), f, indent=2, ensure_ascii=False)

print("✅ Structured JSON saved to:", OUTPUT_JSON_PATH)