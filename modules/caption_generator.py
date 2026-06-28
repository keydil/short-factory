"""
Builds an .ass subtitle file with word-by-word animated captions, cycling
through white / yellow / aqua per word — confirmed from the user's reference
video screenshots. Rendered one word per line with a quick fade, which reads
as far more "produced" than a plain static subtitle track.
"""
import config

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Luckiest Guy,80,&H0000DDFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,2,5,40,40,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:01d}:{m:02d}:{s:05.2f}"


def _rgb_to_ass_bgr(rgb) -> str:
    r, g, b = rgb
    return f"{b:02X}{g:02X}{r:02X}"


def build_caption_file(word_timings: list, output_path: str):
    lines = [ASS_HEADER.format(width=config.VIDEO_WIDTH, height=config.VIDEO_HEIGHT)]
    palette = config.CAPTION_COLOR_CYCLE

    for i, w in enumerate(word_timings):
        start = _format_time(w["start"])
        end = _format_time(w["end"])
        text = w["word"].upper().replace("\n", " ").strip()
        if not text:
            continue
        color_tag = f"\\1c&H{_rgb_to_ass_bgr(palette[i % len(palette)])}&"
        # \fad(60,60) = quick 60ms fade in/out per word; \1c overrides this word's fill colour
        lines.append(f"Dialogue: 0,{start},{end},Caption,,0,0,0,,{{\\fad(60,60){color_tag}}}{text}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)