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
CHUNKS_JSON = Path("class 8 part1/chapter1/modules/m1_chunks.json")
BASE_DIR = Path("class 8 part1/chapter1/modules/chunks/audio/m1")
TIMELINE_FILE = BASE_DIR / "timeline.json"

INTRO_VIDEO = "intro_v0.mp4"
END_VIDEO = "end_v0.mp4"
FINAL_OUTPUT = "chapter1_module1_cinematic.mp4"

SLIDES_DIR = Path("generated_slides_m1")
SLIDES_DIR.mkdir(exist_ok=True)

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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Noto+Sans+Kannada:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; background: #020202; color: white; font-family: 'Inter', 'Noto Sans Kannada'; display: flex; width: {WIDTH}px; height: {HEIGHT}px; }}
            .sidebar {{ width: 450px; padding: 100px 60px; border-right: 1px solid rgba(255,255,255,0.1); }}
            .brand {{ font-size: 22px; font-weight: 700; color: #00c6ff; border-left: 4px solid #00c6ff; padding-left: 20px; letter-spacing: 3px; }}
            .content {{ flex: 1; padding: 100px; display: flex; flex-direction: column; justify-content: center; }}
            .title {{ font-size: 64px; font-weight: 800; margin-bottom: 20px; }}
            .accent {{ width: 100px; height: 6px; background: #00c6ff; margin-bottom: 50px; box-shadow: 0 0 15px #00c6ff; }}
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@800&family=Noto+Sans+Kannada:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ margin:0; background:#020202; color:white; font-family:'Inter','Noto Sans Kannada'; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; width:{WIDTH}px; height:{HEIGHT}px; background-image: radial-gradient(circle at 50% 50%, #001a25 0%, #020202 80%); }}
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
# ENGINE: SLIDE GENERATION
# ==============================

async def generate_assets():
    with open(CHUNKS_JSON, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})

        # 1. Generate Intro Slide
        intro_html = get_intro_slide_html(meta['chapter_title'], meta['module_title'])
        await page.set_content(intro_html)
        await page.screenshot(path=str(SLIDES_DIR / "slide_intro.png"))

        # 2. Generate Content Slides
        for i, segment in enumerate(timeline):
            content_html = get_content_html(segment["display"]["title"], segment["display"]["markdown"])
            await page.set_content(content_html)
            await page.screenshot(path=str(SLIDES_DIR / f"slide_{i}.png"))
        
        await browser.close()

# ==============================
# ENGINE: VIDEO ASSEMBLY
# ==============================

def assemble_video():
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    # Start with Intro Slide (4 seconds)
    all_clips = [
        ImageClip(str(SLIDES_DIR / "slide_intro.png"))
        .with_duration(4.0)
        .with_fps(FPS)
        .with_effects([vfx.FadeIn(1)])
    ]

    # Add Module Content
    for i, segment in enumerate(timeline):
        audio_path = Path(segment["file"].replace("\\", "/")).resolve()
        audio = AudioFileClip(str(audio_path))
        
        clip = (
            ImageClip(str(SLIDES_DIR / f"slide_{i}.png"))
            .with_duration(segment["duration"])
            .with_audio(audio)
            .with_fps(FPS)
            .with_effects([vfx.CrossFadeIn(0.5)])
        )
        all_clips.append(clip)

    main_content = concatenate_videoclips(all_clips, method="compose")

    # Final Wrap with Video Intro/Outro
    intro_vid = VideoFileClip(INTRO_VIDEO).resized((WIDTH, HEIGHT))
    end_vid = VideoFileClip(END_VIDEO).resized((WIDTH, HEIGHT))

    final = concatenate_videoclips([intro_vid, main_content, end_vid], method="compose", padding=-1)
    
    final.write_videofile(
        FINAL_OUTPUT,
        fps=FPS,
        codec="libx264",
        preset="veryfast",
        threads=THREADS,
        ffmpeg_params=["-crf", CRF_VALUE]
    )

if __name__ == "__main__":
    print("🎨 Generating UI Assets...")
    asyncio.run(generate_assets())
    print("🎬 Assembling Cinematic Video...")
    assemble_video()
    print("✅ Done!")