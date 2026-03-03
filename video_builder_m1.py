import os
import json
import asyncio
from pathlib import Path
from moviepy import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx
)
from playwright.async_api import async_playwright

# ==============================
# CONFIG
# ==============================

BASE_DIR = Path("class 8 part1/chapter1/modules/chunks/audio/m1")
TIMELINE_FILE = BASE_DIR / "timeline.json"
OUTPUT_VIDEO = "chapter1_module1.mp4"

SLIDES_DIR = Path("generated_slides_m1")
SLIDES_DIR.mkdir(exist_ok=True)

WIDTH = 1920
HEIGHT = 1080

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
            position: relative;
        }}

        /* Academy Branding */
        .brand {{
            position: absolute;
            top: 60px;
            right: 80px;
            font-size: 28px;
            letter-spacing: 2px;
            font-weight: 600;
            opacity: 0.85;
        }}

        .brand::after {{
            content: "";
            display: block;
            width: 100%;
            height: 2px;
            background: #00c6ff;
            margin-top: 6px;
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
# RENDER HTML → PNG
# ==============================

async def render_slide(html_content, output_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        temp_html = SLIDES_DIR / "temp.html"
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        await page.goto(f"file://{temp_html.resolve()}")
        await page.wait_for_timeout(500)
        await page.screenshot(path=output_path)
        await browser.close()

async def generate_all_slides():
    for i, segment in enumerate(timeline):
        title = segment["display"]["title"]
        markdown = segment["display"]["markdown"]

        html_content = generate_html(title, markdown)
        output_png = SLIDES_DIR / f"slide_{i}.png"

        await render_slide(html_content, output_png)

asyncio.run(generate_all_slides())

# ==============================
# BUILD VIDEO
# ==============================

# ==============================
# BUILD VIDEO
# ==============================

clips = []

for i, segment in enumerate(timeline):

    raw_path = segment["file"]
    audio_path = Path(raw_path.replace("\\", "/")).resolve()

    if not audio_path.exists():
        raise FileNotFoundError(f"Missing audio: {audio_path}")

    duration = segment["duration"]
    img_path = SLIDES_DIR / f"slide_{i}.png"

    audio_clip = AudioFileClip(str(audio_path))

    clip = (
        ImageClip(str(img_path))
        .with_duration(duration)
        .with_audio(audio_clip)
        .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
    )

    clips.append(clip)

final_video = concatenate_videoclips(clips, method="compose")

final_video.write_videofile(
    OUTPUT_VIDEO,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    bitrate="5000k"
)

print("✅ Chapter 1 Module 1 video generated successfully!")

from moviepy import VideoFileClip, concatenate_videoclips, vfx

print("🎬 Merging intro + module + end with smooth fades...")

fade_duration = 1  # seconds

intro_clip = VideoFileClip("intro.mp4")
main_clip = VideoFileClip(OUTPUT_VIDEO)
end_clip = VideoFileClip("end.mp4")

# Match resolution
intro_clip = intro_clip.resized(newsize=main_clip.size)
end_clip = end_clip.resized(newsize=main_clip.size)

# Match FPS
intro_clip = intro_clip.with_fps(30)
main_clip = main_clip.with_fps(30)
end_clip = end_clip.with_fps(30)

# Apply crossfade
main_clip = main_clip.with_effects([vfx.CrossFadeIn(fade_duration)])
end_clip = end_clip.with_effects([vfx.CrossFadeIn(fade_duration)])

# Concatenate with overlap
final_video = concatenate_videoclips(
    [intro_clip, main_clip, end_clip],
    method="compose",
    padding=-fade_duration
)

final_video.write_videofile(
    "chapter1_module1_full.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac",
    bitrate="6000k",
    preset="medium"
)

print("✅ Final cinematic version created!")