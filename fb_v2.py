import os
import json
import asyncio
import multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from moviepy import (
    ImageClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
)
from playwright.async_api import async_playwright

# ==============================
# MACHINE CONFIG (c7g.4xlarge)
# ==============================

TOTAL_CORES = multiprocessing.cpu_count()
MAX_WORKERS = 3              # 3 parallel encoders
THREADS_PER_JOB = 4          # 3 x 4 = 12 cores used
FPS = 30
WIDTH, HEIGHT = 1920, 1080
CRF_VALUE = "23"
PRESET = "ultrafast"

BASE_CLASS_PATH = Path(__file__).parent / "class 8 part1"
INTRO_VIDEO = "intro_v0.mp4"
END_VIDEO = "end_v0.mp4"

print(f"🧠 CPU Cores: {TOTAL_CORES}")
print(f"🚀 Parallel Workers: {MAX_WORKERS}")
print(f"⚙ Threads per Worker: {THREADS_PER_JOB}")

# ==============================
# HTML
# ==============================

def get_content_html(title, markdown_text):
    bullets = ""
    for line in markdown_text.split("\n"):
        if line.strip():
            clean = line.strip().lstrip("- ").lstrip("* ")
            bullets += f"<li>{clean}</li>"

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin:0;
                width:{WIDTH}px;
                height:{HEIGHT}px;
                background:#020202;
                color:white;
                font-family:'Noto Sans Kannada', sans-serif;
                padding:120px;
            }}
            h1 {{ font-size:70px; }}
            li {{ font-size:42px; margin-bottom:25px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <ul>{bullets}</ul>
    </body>
    </html>
    """

def get_intro_html(chapter, module):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin:0;
                width:{WIDTH}px;
                height:{HEIGHT}px;
                background:#020202;
                color:white;
                display:flex;
                flex-direction:column;
                align-items:center;
                justify-content:center;
                font-family:'Noto Sans Kannada', sans-serif;
            }}
            .chapter {{ font-size:80px; font-weight:800; }}
            .module {{ font-size:40px; margin-top:40px; color:#aaa; }}
        </style>
    </head>
    <body>
        <div class="chapter">{chapter}</div>
        <div class="module">{module}</div>
    </body>
    </html>
    """

# ==============================
# VIDEO VALIDATION
# ==============================

def is_video_valid(path: Path):
    if not path.exists():
        return False
    try:
        clip = VideoFileClip(path.as_posix())
        d = clip.duration
        clip.close()
        return d and d > 5
    except:
        return False

# ==============================
# SLIDE GENERATION
# ==============================

async def generate_slides(meta_file, timeline_file, slides_dir):
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    with open(timeline_file, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    slides_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        await page.set_content(get_intro_html(meta["chapter_title"], meta["module_title"]))
        await page.screenshot(path=str(slides_dir / "slide_intro.png"))

        for i, segment in enumerate(timeline):
            await page.set_content(
                get_content_html(
                    segment["display"]["title"],
                    segment["display"]["markdown"]
                )
            )
            await page.screenshot(path=str(slides_dir / f"slide_{i}.png"))

        await browser.close()

# ==============================
# VIDEO ASSEMBLY
# ==============================

def assemble_video(timeline_file, slides_dir, output_path):

    with open(timeline_file, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    clips = []

    clips.append(
        ImageClip((slides_dir / "slide_intro.png").as_posix())
        .with_duration(4)
        .with_fps(FPS)
    )

    for i, segment in enumerate(timeline):
        audio_path = Path(segment["file"].replace("\\", "/")).resolve()

        if not audio_path.exists():
            continue

        audio = AudioFileClip(audio_path.as_posix())

        clip = (
            ImageClip((slides_dir / f"slide_{i}.png").as_posix())
            .with_duration(audio.duration)
            .with_audio(audio)
            .with_fps(FPS)
        )

        clips.append(clip)

    main_video = concatenate_videoclips(clips, method="compose")

    intro_vid = VideoFileClip(INTRO_VIDEO).resized((WIDTH, HEIGHT))
    end_vid = VideoFileClip(END_VIDEO).resized((WIDTH, HEIGHT))

    final = concatenate_videoclips(
        [intro_vid, main_video, end_vid],
        method="compose",
        padding=-1
    )

    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset=PRESET,
        threads=THREADS_PER_JOB,
        ffmpeg_params=["-crf", CRF_VALUE]
    )

# ==============================
# WORKER FUNCTION (REAL PARALLEL)
# ==============================

def process_module(args):

    chapter_path, chunk_file = args

    module_name = chunk_file.stem.replace("_chunks", "")
    audio_dir = chunk_file.parent / "audio" / module_name
    timeline_file = audio_dir / "timeline.json"

    output_path = chapter_path / f"{chapter_path.name}_{module_name}.mp4"

    if is_video_valid(output_path):
        print(f"⏭ Skipping: {output_path.name}")
        return

    print(f"🎬 Rendering: {output_path.name}")

    slides_dir = chapter_path / f"slides_{module_name}"

    asyncio.run(generate_slides(chunk_file, timeline_file, slides_dir))
    assemble_video(timeline_file, slides_dir, output_path.as_posix())

    print(f"✅ Done: {output_path.name}")

# ==============================
# MAIN CONTROLLER
# ==============================

def run_parallel():

    jobs = []

    chapters = sorted([c for c in BASE_CLASS_PATH.iterdir() if c.is_dir()])

    for chapter in chapters:
        modules_chunks = sorted(
            (chapter / "modules" / "chunks").glob("m*_chunks.json")
        )

        for chunk_file in modules_chunks:
            jobs.append((chapter, chunk_file))

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(process_module, jobs)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    print("🚀 TRUE Parallel Video Builder Started")
    run_parallel()
    print("🎉 All Videos Completed")