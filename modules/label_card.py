"""
Renders the big bouncy on-screen text label seen in the reference screenshots
(e.g. "AQUA DOTS", or a wrapped multi-line title like "3 DANGEROUS / TOYS / IN
THE WORLD!"). This is the PRIMARY on-screen text per beat, confirmed visually
from the user's reference frames — separate from the word-by-word spoken
captions in caption_generator.py, which track the narration itself.
"""
import textwrap
from PIL import Image, ImageDraw, ImageFont
import config


def _load_font(size: int):
    try:
        return ImageFont.truetype(config.FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def generate_label_card(text: str, output_path: str, max_chars_per_line: int = 14, font_size: int = 90):
    lines = textwrap.wrap(text.upper(), width=max_chars_per_line) or [text.upper()]
    font = _load_font(font_size)

    line_height = int(font_size * 1.15)
    canvas_w, canvas_h = config.VIDEO_WIDTH, line_height * len(lines) + 80
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (canvas_w - line_w) // 2 - bbox[0]

        # drop shadow first, then the stroked/outlined fill on top
        draw.text((x + 6, y + 8), line, font=font, fill=(0, 0, 0, 130))
        draw.text(
            (x, y), line, font=font,
            fill=config.TEXT_FILL_COLOR, stroke_width=8, stroke_fill=config.TEXT_OUTLINE_COLOR,
        )
        y += line_height

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    img.save(output_path)