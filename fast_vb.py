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
            # Using a custom bullet point for a more premium look
            bullets += f"<li><span class='bullet-icon'></span>{line.strip()}</li>"

    return f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Noto+Sans+Kannada:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 100px;
            width: {WIDTH}px;
            height: {HEIGHT}px;
            background-color: #050505;
            background-image: 
                radial-gradient(circle at 0% 0%, rgba(0, 198, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 100% 100%, rgba(0, 198, 255, 0.05) 0%, transparent 50%);
            font-family: 'Inter', 'Noto Sans Kannada', sans-serif;
            color: #e0e0e0;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        /* Premium Brand Header */
        .brand-container {{
            position: absolute;
            top: 60px;
            right: 80px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }}

        .brand {{
            font-size: 24px;
            letter-spacing: 4px;
            font-weight: 700;
            color: #00c6ff;
            text-transform: uppercase;
            padding: 10px 20px;
            border: 1px solid rgba(0, 198, 255, 0.3);
            background: rgba(255, 255, 255, 0.03);
            border-radius: 4px;
            backdrop-filter: blur(10px);
        }}

        .title {{
            font-size: 72px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 20px;
            line-height: 1.2;
            text-shadow: 0px 4px 20px rgba(0,0,0,0.5);
        }}

        .divider {{
            width: 120px;
            height: 6px;
            background: linear-gradient(90deg, #00c6ff, #0072ff);
            margin-bottom: 60px;
            border-radius: 3px;
        }}

        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        li {{
            font-size: 44px;
            line-height: 1.5;
            margin-bottom: 35px;
            display: flex;
            align-items: flex-start;
            color: #cccccc;
            font-weight: 400;
        }}

        .bullet-icon {{
            width: 12px;
            height: 12px;
            background: #00c6ff;
            margin-top: 24px;
            margin-right: 25px;
            flex-shrink: 0;
            border-radius: 2px;
            box-shadow: 0 0 15px rgba(0, 198, 255, 0.6);
        }}
    </style>
    </head>
    <body>
        <div class="brand-container">
            <div class="brand">SRINIVAS IAS ACADEMY</div>
        </div>
        
        <div class="title">{title}</div>
        <div class="divider"></div>
        
        <ul>
            {bullets}
        </ul>
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