import os
import json
import asyncio
from pathlib import Path
from typing import List, Literal
from openai import OpenAI
from pydantic import BaseModel, Field

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path("class 8 part1")
PROMPT_PATH = Path("promts/generate_chunks_strict.txt")

MODEL_NAME = "gpt-4.1"
TEMPERATURE = 0.2
MAX_CONCURRENT_REQUESTS = 5   # increase carefully

client = OpenAI(api_key="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")

# ============================================================
# SCHEMA
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
# LOAD PROMPT TEMPLATE
# ============================================================

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    structuring_prompt_template = f.read()

# ============================================================
# BLOCKING OPENAI CALL WRAPPER
# ============================================================

def generate_chunks_blocking(final_prompt):
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
    return response.output_parsed

# ============================================================
# ASYNC PROCESSOR
# ============================================================

async def process_module(module_path: Path, semaphore):

    async with semaphore:

        elite_path = module_path.with_name(module_path.stem + "_elite.txt")
        if not elite_path.exists():
            print(f"⚠ Elite missing: {module_path}")
            return

        chunks_folder = module_path.parent / "chunks"
        chunks_folder.mkdir(exist_ok=True)

        output_path = chunks_folder / f"{module_path.stem}_chunks.json"

        if output_path.exists():
            print(f"⏭ Skipped: {module_path}")
            return

        print(f"🚀 Structuring: {module_path}")

        try:
            with open(module_path, "r", encoding="utf-8") as f:
                module_data = json.load(f)

            with open(elite_path, "r", encoding="utf-8") as f:
                elite_text = f.read()

            chapter_title = module_data["chapter_title"]
            module_id = module_data["module_metadata"]["module_id"]
            module_title = module_data["module_metadata"]["module_title"]

            final_prompt = f"""
{structuring_prompt_template}

Chapter Title: {chapter_title}
Module ID: {module_id}
Module Title: {module_title}

ELITE SCRIPT:
{elite_text}
"""

            # 🔥 run blocking call in background thread
            structured_output = await asyncio.to_thread(
                generate_chunks_blocking,
                final_prompt
            )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured_output.model_dump(), f, indent=2, ensure_ascii=False)

            print(f"✅ Saved: {output_path}")

        except Exception as e:
            print(f"❌ Error: {module_path} -> {e}")

# ============================================================
# MAIN
# ============================================================

async def main():

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    module_files = list(BASE_DIR.rglob("modules/m*.json"))

    print(f"📦 Found {len(module_files)} modules")

    tasks = [
        process_module(path, semaphore)
        for path in module_files
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())