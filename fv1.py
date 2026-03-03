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
# CONFIG (Linux Paths)
# ==============================
# Normalizing input paths for Linux environment
BASE_PATH = Path("class 8 part1/chapter1/modules")
CHUNKS_JSON = BASE_PATH / "chunks/m1_chunks.json"
AUDIO_DIR = BASE_PATH / "chunks/audio/m1"
TIMELINE_FILE = AUDIO_DIR / "timeline.json"

INTRO_VIDEO = "intro_v0.mp4"
END_VIDEO = "end_v0.mp4"
FINAL_OUTPUT = "chapter1_module1_linux_ready.mp4"

SLIDES_DIR = Path("generated_slides_m1")
SLIDES_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1920, 1080
FPS = 30
THREADS = 12
CRF_VALUE = "20"

# ==============================
# HTML TEMPLATES
# ==============================

def get_content_html(title, markdown_text):
    bullets = "".join([f"<li><span class='bullet-node'></span>{line.strip().lstrip('- *')}</li>" 
                       for line in markdown_text.split("\n") if line.strip()])
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; background: #020202; color: white; font-family: 'Noto Sans Kannada', sans-serif; display: flex; width: {WIDTH}px; height: {HEIGHT}px; }}
            .sidebar {{ width: 450px; padding: 100px 60px; border-right: 1px solid rgba(255,255,255,0.1); }}
            .brand {{ font-size: 22px; font-weight: 700; color: #00c6ff; border-left: 4px solid #00c6ff; padding-left: 20px; letter-spacing: 3px; }}
            .content {{ flex: 1; padding: 100px; display: flex; flex-direction: column; justify-content: center; }}
            .title {{ font-size: 64px; font-weight: 800; margin-bottom: 20px; }}
            .accent {{ width: 100px; height: 6px; background: #00c6ff; margin-bottom: 50px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ font-size: 38px; margin-bottom: 35px; display: flex; align-items: flex-start; color: #d0d0d0; }}
            .bullet-node {{ width: 8px; height: 28px; background: #00c6ff; margin: 12px 25px 0 0; flex-shrink: 0; }}
        </style>
    </head>
    <body>
        <div class="sidebar"><div class="brand">SRINIVAS IAS<br>ACADEMY</div></div>
        <div class="content"><div class="title">{title}</div><div class="accent"></div><ul>{bullets}</ul></div>
    </body>
    </html>
    """

def get_intro_slide_html(chapter, module):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin:0; background:#020202; color:white; font-family:'Noto Sans Kannada', sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; width:{WIDTH}px; height:{HEIGHT}px; background-image: radial-gradient(circle at 50% 50%, #001a25 0%, #020202 80%); }}
            .tag {{ font-size: 30px; color: #00c6ff; border: 2px solid #00c6ff; padding: 10px 40px; border-radius: 50px; margin-bottom: 40px; }}
            .chapter {{ font-size: 80px; font-weight: 800; max-width: 1500px; line-height: 1.2; }}
            .bar {{ width: 300px; height: 4px; background: linear-gradient(90deg, transparent, #00c6ff, transparent); margin: 50px 0; }}
            .module {{ font-size: 45px; color: #aaa; }}
        </style>
    </head>
    <body>
        <div class="tag">8ನೇ ತರಗತಿ ಸಮಾಜ ವಿಜ್ಞಾನ</div>
        <div class="chapter">{chapter}</div>
        <div class="bar"></div>
        <div class="module">{module}</div>
    </body>
    </html>
    """

# ==============================
# ASSET GENERATION
# ==============================

async def generate_assets():
    # Load metadata and timeline
    with open(CHUNKS_JSON, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        # Intro Slide
        intro_html = get_intro_slide_html(meta['chapter_title'], meta['module_title'])
        await page.set_content(intro_html)
        await page.screenshot(path=str(SLIDES_DIR / "slide_intro.png"))

        # Content Slides
        for i, segment in enumerate(timeline):
            content_html = get_content_html(segment["display"]["title"], segment["display"]["markdown"])
            await page.set_content(content_html)
            await page.screenshot(path=str(SLIDES_DIR / f"slide_{i}.png"))
        
        await browser.close()

# ==============================
# VIDEO ASSEMBLY
# ==============================

def assemble_video():
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    # 1. Intro Slide (The one you requested with Class 8 info)
    intro_img_path = (SLIDES_DIR / "slide_intro.png").as_posix()
    all_clips = [
        ImageClip(intro_img_path)
        .with_duration(4.0)
        .with_fps(FPS)
        .with_effects([vfx.FadeIn(1)])
    ]

    # 2. Add Module Content (Normalizing Linux Paths)
    for i, segment in enumerate(timeline):
        # Path Normalization: Replacing Windows backslashes with Linux forward slashes
        raw_audio_path = segment["file"].replace("\\", "/")
        audio_path = Path(raw_audio_path).resolve()
        
        if not audio_path.exists():
            print(f"⚠️ Warning: Missing audio file at {audio_path}")
            continue

        audio = AudioFileClip(audio_path.as_posix())
        slide_img = (SLIDES_DIR / f"slide_{i}.png").as_posix()
        
        clip = (
            ImageClip(slide_img)
            .with_duration(segment["duration"])
            .with_audio(audio)
            .with_fps(FPS)
            .with_effects([vfx.CrossFadeIn(0.5)])
        )
        all_clips.append(clip)

    main_video = concatenate_videoclips(all_clips, method="compose")

    # 3. Wrapping with Intro/Outro Videos
    intro_vid = VideoFileClip(INTRO_VIDEO).resized((WIDTH, HEIGHT)).with_fps(FPS)
    end_vid = VideoFileClip(END_VIDEO).resized((WIDTH, HEIGHT)).with_fps(FPS)

    # Padding -1 creates a 1s crossfade between clips
    final = concatenate_videoclips([intro_vid, main_video, end_vid], method="compose", padding=-1)
    
    final.write_videofile(
        FINAL_OUTPUT,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast",
        threads=THREADS,
        ffmpeg_params=["-crf", CRF_VALUE]
    )

if __name__ == "__main__":
    print("🚀 Starting Linux-Normalized Render Process...")
    asyncio.run(generate_assets())
    assemble_video()
    print(f"✨ Success! Video saved as: {FINAL_OUTPUT}")