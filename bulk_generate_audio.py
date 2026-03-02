import os
import json
import wave
import random
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech

# ==========================================
# CONFIG
# ==========================================

BASE_DIR = Path("class 8 part1")
API_ENDPOINT = "texttospeech.googleapis.com"
MODEL = "gemini-2.5-pro-tts"
MAX_WORKERS = 3
PAUSE_SECONDS = 0.4

# ==========================================
# VOICE OPTIONS (Random per module)
# ==========================================

VOICE_OPTIONS = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda",
    "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus",
    "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome",
    "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Schedar", "Gacrux", "Pulcherrima",
    "Achird", "Zubenelgenubi", "Vindemiatrix",
    "Sadachbia", "Sadaltager", "Sulafat"
]

# ==========================================
# TTS CLIENT
# ==========================================

client = texttospeech.TextToSpeechClient(
    client_options=ClientOptions(api_endpoint=API_ENDPOINT)
)

AUDIO_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    speaking_rate=1.05,
    pitch=0
)

# ==========================================
# SYNTHESIZE
# ==========================================

def synthesize(text, filename, voice):
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=voice,
        audio_config=AUDIO_CONFIG,
    )

    with open(filename, "wb") as out:
        out.write(response.audio_content)

# ==========================================
# GENERATE SEGMENT
# ==========================================

def generate_segment(i, chunk, out_dir, voice):

    fname = out_dir / f"seg_{i}.wav"

    if not fname.exists():
        print("Generating:", fname)
        synthesize(chunk["script"].strip(), fname, voice)

    with wave.open(str(fname), 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)

    return {
        "index": i,
        "file": str(fname),
        "duration": duration,
        "display": chunk.get("display", {})
    }

# ==========================================
# MERGE WAV
# ==========================================

def merge_wav_files(segments, output_path):

    first = segments[0]["file"]

    with wave.open(first, 'rb') as wf:
        params = wf.getparams()
        rate = wf.getframerate()

    def silence(duration):
        samples = int(duration * rate)
        return (np.zeros(samples)).astype(np.int16).tobytes()

    timeline = []
    current_time = 0

    with wave.open(str(output_path), 'wb') as out:
        out.setparams(params)

        for seg in segments:
            with wave.open(seg["file"], 'rb') as wf:
                audio = wf.readframes(wf.getnframes())
                out.writeframes(audio)

            start = current_time
            end = start + seg["duration"]

            timeline.append({
                "file": seg["file"],
                "start": round(start, 2),
                "end": round(end, 2),
                "duration": round(seg["duration"], 2),
                "display": seg["display"]
            })

            current_time = end + PAUSE_SECONDS
            out.writeframes(silence(PAUSE_SECONDS))

    return timeline

# ==========================================
# PROCESS MODULE
# ==========================================

def process_module(chunk_file):

    print("\n📦 Processing:", chunk_file)

    with open(chunk_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data["chunks"]

    module_name = chunk_file.stem.replace("_chunks", "")
    audio_dir = chunk_file.parent / "audio" / module_name
    audio_dir.mkdir(parents=True, exist_ok=True)

    # 🔀 Pick random voice for this module
    selected_voice = random.choice(VOICE_OPTIONS)
    print(f"🎙 Using voice: {selected_voice}")

    voice = texttospeech.VoiceSelectionParams(
        name=selected_voice,
        language_code="kn-IN",
        model_name=MODEL
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(generate_segment, i, chunk, audio_dir, voice)
            for i, chunk in enumerate(chunks)
        ]

        segments = [f.result() for f in as_completed(futures)]

    segments = sorted(segments, key=lambda x: x["index"])

    final_output = audio_dir / "final_module.wav"
    timeline = merge_wav_files(segments, final_output)

    with open(audio_dir / "timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)

    print("✅ Completed:", final_output)

# ==========================================
# MAIN
# ==========================================

def main():

    chunk_files = list(BASE_DIR.rglob("modules/chunks/*.json"))

    print(f"\n🔍 Found {len(chunk_files)} modules\n")

    for chunk_file in chunk_files:
        process_module(chunk_file)

    print("\n🎉 All modules processed successfully.")

if __name__ == "__main__":
    main()