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

# INTRO_VIDEO = "intro.mp4"
# END_VIDEO = "end.mp4"

FINAL_OUTPUT = "chapter1_module1_full_fast.mp4"

SLIDES_DIR = Path("generated_slides_m1")
SLIDES_DIR.mkdir(exist_ok=True)

WIDTH = 1920
HEIGHT = 1080
FPS = 30
THREADS =12   # optimized for 16 vCPU machine
CRF_VALUE = "20"  # 18 = near lossless, 20 = very high quality

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
            # Clean up potential markdown characters like '-' or '*'
            clean_line = line.strip().lstrip('- ').lstrip('* ')
            bullets += f"<li><span class='bullet-icon'></span>{clean_line}</li>"

    return f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Noto+Sans+Kannada:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
            width: {WIDTH}px;
            height: {HEIGHT}px;
            background-color: #050505;
            font-family: 'Inter', 'Noto Sans Kannada', sans-serif;
            color: #ffffff;
            display: flex;
            overflow: hidden;
        }}

        /* Left Side - Brand Strip */
        .sidebar {{
            width: 350px;
            height: 100%;
            background: linear-gradient(180deg, #0a0a0a 0%, #001a25 100%);
            border-right: 1px solid rgba(0, 198, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}

        .brand-vertical {{
            transform: rotate(-90deg);
            white-space: nowrap;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 12px;
            color: #00c6ff;
            text-transform: uppercase;
            opacity: 0.9;
            text-shadow: 0 0 20px rgba(0, 198, 255, 0.4);
        }}

        /* Right Side - Content Area */
        .content {{
            flex-grow: 1;
            padding: 100px 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            background: radial-gradient(circle at 100% 0%, rgba(0, 198, 255, 0.05) 0%, transparent 40%);
        }}

        .title {{
            font-size: 76px;
            font-weight: 800;
            margin-bottom: 30px;
            line-height: 1.1;
            background: linear-gradient(to right, #ffffff, #bbbbbb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .divider {{
            width: 100px;
            height: 8px;
            background: #00c6ff;
            margin-bottom: 50px;
            border-radius: 4px;
            box-shadow: 0 4px 15px rgba(0, 198, 255, 0.3);
        }}

        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        li {{
            font-size: 42px;
            line-height: 1.4;
            margin-bottom: 40px;
            display: flex;
            align-items: flex-start;
            color: #d1d1d1;
            font-weight: 400;
            animation: fadeIn 0.8s ease-out;
        }}

        .bullet-icon {{
            width: 16px;
            height: 16px;
            background: #00c6ff;
            margin-top: 22px;
            margin-right: 30px;
            flex-shrink: 0;
            border-radius: 50%; /* Rounded for a softer premium feel */
            box-shadow: 0 0 12px rgba(0, 198, 255, 0.8);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateX(20px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
    </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand-vertical">SRINIVAS IAS ACADEMY</div>
        </div>
        
        <div class="content">
            <div class="title">{title}</div>
            <div class="divider"></div>
            <ul>
                {bullets}
            </ul>
        </div>
    </body>
    </html>
    """
# ==============================
# GENERATE SLIDES (Optimized)
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
# BUILD MAIN SLIDE CLIPS
# ==============================

print("🎬 Building slide clips...")

slide_clips = []

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
        .with_fps(FPS)
        .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
    )

    slide_clips.append(clip)

# main_video = concatenate_videoclips(slide_clips, method="compose")
main_video = concatenate_videoclips(slide_clips)
# ==============================
# ADD INTRO + END WITH CROSSFADE
# ==============================

print("🎞 Adding intro and end...")

fade_duration = 1

# intro_clip = VideoFileClip(INTRO_VIDEO).with_fps(FPS)
# end_clip = VideoFileClip(END_VIDEO).with_fps(FPS)

# Resize only if needed
# if intro_clip.size != main_video.size:
#     intro_clip = intro_clip.resized(main_video.size)

# if end_clip.size != main_video.size:
#     end_clip = end_clip.resized(main_video.size)

# main_video = main_video.with_effects([vfx.CrossFadeIn(fade_duration)])
# end_clip = end_clip.with_effects([vfx.CrossFadeIn(fade_duration)])

# final_video = concatenate_videoclips(
#     [intro_clip, main_video, end_clip],
#     method="compose",
#     padding=-fade_duration
# )
# Optional crossfade at beginning only
main_video = main_video.with_effects([vfx.CrossFadeIn(fade_duration)])

final_video = main_video
# ==============================
# FINAL EXPORT (Optimized)
# ==============================

print("🚀 Rendering final video...")

final_video.write_videofile(
    FINAL_OUTPUT,
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    preset="veryfast",
    threads=THREADS,
    ffmpeg_params=["-crf", CRF_VALUE]
)

print("✅ Final cinematic version created successfully!")