import os
import json
import asyncio
from markdown import markdown
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from playwright.async_api import async_playwright

# ==============================
# CONFIG
# ==============================

WIDTH = 1280
HEIGHT = 720

HTML_DIR = "slides_html"
PNG_DIR = "slides_png"

os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)


# ==============================
# HTML TEMPLATE
# ==============================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@400;600&display=swap" rel="stylesheet">

<style>
body {{
  margin: 0;
  width: 1280px;
  height: 720px;
  font-family: 'Noto Sans Kannada', sans-serif;
  background: white;
}}

.header {{
  height: 100px;
  background: #002147;
}}

.footer {{
  height: 80px;
  background: #002147;
}}

.container {{
  padding: 40px 80px;
}}

h1 {{
  color: #003366;
  font-size: 42px;
  margin-bottom: 30px;
}}

.content {{
  font-size: 30px;
  color: #222;
  line-height: 1.6;
}}
</style>
</head>

<body>

<div class="header"></div>

<div class="container">
<h1>{title}</h1>
<div class="content">
{markdown_content}
</div>
</div>

<div class="footer"></div>

</body>
</html>
"""


# ==============================
# STEP 1: GENERATE HTML
# ==============================

def generate_html_slides(timeline):

    html_files = []

    for chunk in timeline:

        title = chunk["display"]["title"]
        md_content = markdown(chunk["display"]["markdown"])

        html_content = HTML_TEMPLATE.format(
            title=title,
            markdown_content=md_content
        )

        html_path = os.path.join(HTML_DIR, f"{chunk['chunk_id']}.html")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        html_files.append((chunk, html_path))

    return html_files


# ==============================
# STEP 2: RENDER HTML → PNG
# ==============================

async def render_html_to_png(html_path, output_path):

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        await page.goto(f"file://{os.path.abspath(html_path)}")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=output_path)
        await browser.close()


async def render_all_slides(html_files):

    for chunk, html_path in html_files:

        png_path = os.path.join(PNG_DIR, f"{chunk['chunk_id']}.png")
        await render_html_to_png(html_path, png_path)

    print("✅ PNG slides generated.")


# ==============================
# STEP 3: CREATE FINAL VIDEO
# ==============================

def generate_video(timeline, output_name="final_course.mp4"):

    clips = []

    for chunk in timeline:

        img_path = os.path.join(PNG_DIR, f"{chunk['chunk_id']}.png")
        audio_path = chunk["file"]
        duration = chunk["duration"]

        img_clip = ImageClip(img_path).set_duration(duration)
        audio_clip = AudioFileClip(audio_path)

        final_clip = img_clip.set_audio(audio_clip)

        clips.append(final_clip)

    final_video = concatenate_videoclips(clips, method="compose")

    print("🎬 Rendering final video...")
    final_video.write_videofile(
        output_name,
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    print("🎉 Video completed!")


# ==============================
# MAIN EXECUTION
# ==============================

def main():

    with open("timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)

    html_files = generate_html_slides(timeline)

    asyncio.run(render_all_slides(html_files))

    generate_video(timeline)


if __name__ == "__main__":
    main()