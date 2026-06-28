"""
Generates a faint, tiled channel-handle watermark across the whole frame,
like the diagonal "YT: 3INTHEWORLD" text seen in the reference screenshots.
Mainly a basic deterrent against other accounts re-uploading your videos as
their own.
"""
from PIL import Image, ImageDraw, ImageFont
import config


def generate_watermark(text: str, output_path: str, opacity: int = 60, font_size: int = 34):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(config.FONT_PATH, font_size)
    except OSError:
        font = ImageFont.load_default()

    label = text.upper()
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    step_x, step_y = tw + 140, th + 170
    for y in range(-step_y, h + step_y, step_y):
        for x in range(-step_x, w + step_x, step_x):
            draw.text((x, y), label, font=font, fill=(255, 255, 255, opacity))

    img.save(output_path)