import json
import asyncio
import vertexai
from pathlib import Path
from vertexai.generative_models import GenerativeModel

# ==========================================
# CONFIG
# ==========================================

PROJECT_ID = "lively-aloe-411504"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-pro"

BASE_DIR = Path("class 8 part1")
MAX_CONCURRENT_REQUESTS = 5

# ==========================================
# INIT VERTEX
# ==========================================

vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_NAME)

# ==========================================
# BLOCKING FUNCTION (runs in thread)
# ==========================================

def generate_content_blocking(prompt):
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "top_p": 0.9
        }
    )
    return response.text

# ==========================================
# ASYNC MODULE PROCESSOR
# ==========================================

async def generate_for_module(module_path: Path, semaphore):

    async with semaphore:

        output_path = module_path.with_name(module_path.stem + "_elite.txt")

        if output_path.exists():
            print(f"⏭ Skipped: {module_path}")
            return

        print(f"🚀 Processing: {module_path}")

        try:
            with open(module_path, "r", encoding="utf-8") as f:
                module_data = json.load(f)

            chapter_title = module_data["chapter_title"]
            module_title = module_data["module_metadata"]["module_title"]
            section_content = module_data["section_content"]

            elite_prompt = f"""
You are an expert academic script writer creating high-clarity instructional content for Text-To-Speech delivery.

ROLE:
Convert the provided academic content into a polished, classroom-ready teaching script.

NON-NEGOTIABLE OUTPUT RULES:

1. Output ONLY the final teaching script.
2. Do NOT include meta text such as:
   - "Here is the script"
   - "This module explains"
   - Any notes, comments, formatting explanations, or system messages
3. Do NOT mention chapter name, module name, or any metadata.
4. Do NOT add external information beyond the provided content.
5. Do NOT summarise unless the source itself contains a summary.
6. Do NOT use bullet points unless conceptually required for clarity.
7. Do NOT use special characters like &, %, /, :, ;, *, etc.
8. Do NOT use numbering unless academically necessary.

TTS OPTIMIZATION RULES:

1. Expand ALL abbreviations into full forms.
   Examples:
   - "ಸಾ.ಶ.ಪೂ." → "ಸಾಮಾನ್ಯ ಶಕ ಪೂರ್ವ"
   - "ಕ್ರಿ.ಶ." → "ಕ್ರಿಸ್ತ ಶಕ"
   - "ಇ.ಸ." → "ಈಸವಿ"
   - Any shortened academic or historical form must be expanded.

2. Convert symbolic or numeric expressions into spoken-friendly format when appropriate.
   - 261 → ಎರಡು ನೂರು ಅರವತ್ತೊಂದು
   - Avoid raw numerals when clarity requires full verbal expression.

3. Write in smooth, natural spoken Kannada suitable for classroom explanation.
4. Maintain academic depth but ensure clarity for learners.
5. Use clear logical flow:
   - Concept introduction
   - Explanation
   - Illustration if present in source
   - Concept reinforcement if present in source

STYLE REQUIREMENTS:

- Tone: Scholarly yet conversational.
- Flow: Structured, coherent, and logically progressive.
- Sentences: Medium length for natural voice modulation.
- Avoid overly long complex sentences that break TTS rhythm.
- Preserve conceptual precision.

CONTENT CONSTRAINT:

Use ONLY the content provided below.
Do not infer, assume, or expand beyond it.

Provided Content:
{section_content}
"""

            # 🔥 Run blocking Gemini call in separate thread
            elite_output = await asyncio.to_thread(
                generate_content_blocking,
                elite_prompt
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(elite_output)

            print(f"✅ Saved: {output_path}")

        except Exception as e:
            print(f"❌ Error: {module_path} -> {e}")

# ==========================================
# MAIN
# ==========================================

async def main():

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    module_files = list(BASE_DIR.rglob("modules/m*.json"))

    print(f"📦 Found {len(module_files)} modules")

    tasks = [
        generate_for_module(path, semaphore)
        for path in module_files
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())