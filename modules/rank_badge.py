"""
Draws a "#3 / #2 / #1" rank badge as a transparent PNG, purely with code via
Pillow — no external image asset needed. Used to overlay on top of the video
for 'top3' format content, which is the single most recognizable visual cue
of that format (it's what makes it read as a countdown, not just a list).
"""
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "arialbd.ttf",                                            # Windows
    "Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Linux (common default)
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",      # macOS
]


def _load_font(size: int):
    for candidate in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    # Last resort — won't look great at this size, but the pipeline won't crash.
    return ImageFont.load_default()


def generate_rank_badge(number: int, output_path: str, diameter: int = 280):
    img = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gold-ringed dark circle, the classic "countdown badge" look
    draw.ellipse([6, 6, diameter - 6, diameter - 6], fill=(15, 15, 15, 235),
                 outline=(255, 200, 0, 255), width=10)

    text = f"#{number}"
    font = _load_font(int(diameter * 0.42))
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((diameter - text_w) / 2 - bbox[0], (diameter - text_h) / 2 - bbox[1]),
        text, font=font, fill=(255, 200, 0, 255),
    )

    img.save(output_path)
