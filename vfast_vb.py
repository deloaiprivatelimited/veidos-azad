import os
import json
import asyncio
from pathlib import Path
from moviepy import (
    ImageClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx
)
from playwright.async_api import async_playwright

# ==============================
# CONFIG
# ==============================

BASE_DIR = Path("class 8 part1/chapter1/modules/chunks/audio/m1")
TIMELINE_FILE = BASE_DIR / "timeline.json"

INTRO_VIDEO = "intro.mp4"
END_VIDEO = "end.mp4"

FINAL_OUTPUT = "chapter1_module1_full_gpu_fast.mp4"

SLIDES_DIR = Path("generated_slides_m1")
SLIDES_DIR.mkdir(exist_ok=True)

WIDTH = 1920
HEIGHT = 1080
FPS = 30

THREADS = 16  # use all vCPUs

# NVENC Quality (lower = better quality)
NVENC_CQ = "23"   # 18–28 range
NVENC_PRESET = "p2"  # p1 fastest, p7 highest quality

FADE_DURATION = 0.4  # shorter fade = faster processing

# ==============================
# LOAD TIMELINE
# ==============================

with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
    timeline = json.load(f)

# ==============================
# HTML TEMPLATE
# ==============================

def generate_html(title, markdown_text):
    bullets = ""
    for line in markdown_text.split("\n"):
        if line.strip():
            bullets += f"<li>{line}</li>"

    return f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 80px;
            width: {WIDTH}px;
            height: {HEIGHT}px;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            font-family: 'Noto Sans Kannada', sans-serif;
            color: white;
        }}

        .brand {{
            position: absolute;
            top: 60px;
            right: 80px;
            font-size: 28px;
            letter-spacing: 2px;
            font-weight: 600;
            opacity: 0.85;
        }}

        .title {{
            font-size: 64px;
            font-weight: bold;
            margin-top: 120px;
            margin-bottom: 40px;
        }}

        .divider {{
            width: 200px;
            height: 4px;
            background: #00c6ff;
            margin-bottom: 40px;
        }}

        ul {{
            font-size: 42px;
            line-height: 1.6;
        }}

        li {{
            margin-bottom: 20px;
        }}
    </style>
    </head>

    <body>
        <div class="brand">SRINIVAS IAS ACADEMY</div>
        <div class="title">{title}</div>
        <div class="divider"></div>
        <ul>
            {bullets}
        </ul>
    </body>
    </html>
    """

# ==============================
# GENERATE SLIDES
# ==============================

async def generate_all_slides():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT}
        )

        temp_html = SLIDES_DIR / "temp.html"

        for i, segment in enumerate(timeline):
            title = segment["display"]["title"]
            markdown = segment["display"]["markdown"]

            html_content = generate_html(title, markdown)

            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)

            await page.goto(f"file://{temp_html.resolve()}")
            await page.wait_for_load_state("networkidle")

            output_png = SLIDES_DIR / f"slide_{i}.png"
            await page.screenshot(path=output_png)

        await browser.close()

print("🎨 Generating slides...")
asyncio.run(generate_all_slides())
print("✅ Slides generated.")

# ==============================
# BUILD MAIN VIDEO
# ==============================

print("🎬 Building slide clips...")

slide_clips = []

for i, segment in enumerate(timeline):

    raw_path = segment["file"]
    audio_path = Path(raw_path.replace("\\", "/")).resolve()

    duration = segment["duration"]
    img_path = SLIDES_DIR / f"slide_{i}.png"

    audio_clip = AudioFileClip(str(audio_path))

    clip = (
        ImageClip(str(img_path))
        .with_duration(duration)
        .with_audio(audio_clip)
        .with_fps(FPS)
        .with_effects([
            vfx.FadeIn(FADE_DURATION),
            vfx.FadeOut(FADE_DURATION)
        ])
    )

    slide_clips.append(clip)

main_video = concatenate_videoclips(slide_clips, method="compose")

# ==============================
# ADD INTRO + END
# ==============================

print("🎞 Adding intro and end...")

intro_clip = VideoFileClip(INTRO_VIDEO).with_fps(FPS)
end_clip = VideoFileClip(END_VIDEO).with_fps(FPS)

if intro_clip.size != main_video.size:
    intro_clip = intro_clip.resized(main_video.size)

if end_clip.size != main_video.size:
    end_clip = end_clip.resized(main_video.size)

main_video = main_video.with_effects([vfx.CrossFadeIn(FADE_DURATION)])
end_clip = end_clip.with_effects([vfx.CrossFadeIn(FADE_DURATION)])

final_video = concatenate_videoclips(
    [intro_clip, main_video, end_clip],
    method="compose",
    padding=-FADE_DURATION
)

# ==============================
# FINAL EXPORT (GPU MAX SPEED)
# ==============================

print("🚀 Rendering with NVENC GPU...")

final_video.write_videofile(
    FINAL_OUTPUT,
    fps=FPS,
    codec="h264_nvenc",      # 🔥 GPU encoding
    audio_codec="aac",
    preset=NVENC_PRESET,
    threads=THREADS,
    ffmpeg_params=[
        "-cq", NVENC_CQ,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart"
    ]
)

print("✅ Ultra-fast GPU cinematic version created!")