import os
import tiktoken

# ==========================================
# CONFIG
# ==========================================

ROOT_FOLDER = "class 8 part1"
PROMPT_FILE = os.path.join("promts", "generate_chunks.txt")
MODEL_NAME = "gpt-4.1"  # or gpt-4o-2024-08-06

# ==========================================
# TOKENIZER
# ==========================================

try:
    encoding = tiktoken.encoding_for_model(MODEL_NAME)
except KeyError:
    encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# ==========================================
# COUNT PROMPT TOKENS
# ==========================================

total_prompt_tokens = 0
total_module_tokens = 0
module_count = 0

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    prompt_content = f.read()
    total_prompt_tokens = count_tokens(prompt_content)

# ==========================================
# COUNT MODULE JSON TOKENS
# ==========================================

for root, dirs, files in os.walk(ROOT_FOLDER):
    if "modules" in root and "chunks" not in root:
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tokens = count_tokens(content)
                total_module_tokens += tokens
                module_count += 1

# ==========================================
# RESULTS
# ==========================================

print("\n========== TOKEN REPORT ==========\n")

print(f"Chunk Prompt Tokens: {total_prompt_tokens:,}")
print(f"Total Module JSON Tokens: {total_module_tokens:,}")
print(f"Number of Modules: {module_count}")

total_generation_tokens = total_module_tokens + (total_prompt_tokens * module_count)

print("\n-----------------------------------")
print(f"Total Tokens Sent to Model: {total_generation_tokens:,}")
print("-----------------------------------\n")