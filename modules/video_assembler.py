"""
Stitches the visuals + voiceover + background music into the final vertical
video, overlays label cards / rank badges / watermark, mixes in SFX, then
(optionally) burns word-by-word captions on top with ffmpeg directly (more
reliable for styled/animated captions than rendering them purely inside moviepy).
"""
import os
import subprocess
from PIL import Image as PILImage
if not hasattr(PILImage, "ANTIALIAS"):
    PILImage.ANTIALIAS = PILImage.LANCZOS  # Pillow 10+ renamed it
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips,
)
from moviepy.video.fx.all import crop
from moviepy.audio.fx.all import audio_loop
import config
from modules import sfx_manager, rank_badge, label_card, watermark


def _clip_for_segment(visual: dict, duration: float):
    if visual["type"] == "video":
        clip = VideoFileClip(visual["path"])
        clip = clip.subclip(0, min(duration, clip.duration))
    else:
        # Ken Burns style slow zoom on static images - the classic "fake camera move"
        clip = ImageClip(visual["path"]).set_duration(duration).resize(lambda t: 1 + 0.04 * t)

    clip = clip.resize(height=config.VIDEO_HEIGHT)
    if clip.w < config.VIDEO_WIDTH:
        clip = clip.resize(width=config.VIDEO_WIDTH)

    clip = crop(
        clip, x_center=clip.w / 2, y_center=clip.h / 2,
        width=config.VIDEO_WIDTH, height=config.VIDEO_HEIGHT,
    )
    return clip.set_duration(duration)


def assemble_video(visuals: list, segment_durations: list, segments: list,
                    voice_path: str, music_path, caption_path: str, output_path: str):
    clips = [_clip_for_segment(v, d) for v, d in zip(visuals, segment_durations)]

    # --- Overlay rank badges on segments that have a rank (off by default, see config) ---
    if config.ENABLE_RANK_BADGES and config.CONTENT_FORMAT == "top3":
        for i, seg in enumerate(segments):
            rank = seg.get("rank")
            if rank is not None and i < len(clips):
                badge_path = os.path.join(config.TEMP_DIR, f"badge_{rank}.png")
                if not os.path.exists(badge_path):
                    rank_badge.generate_rank_badge(rank, badge_path)
                badge_clip = (
                    ImageClip(badge_path)
                    .set_duration(clips[i].duration)
                    .set_position(("right", "top"))
                    .margin(right=40, top=80, opacity=0)
                )
                clips[i] = CompositeVideoClip(
                    [clips[i], badge_clip],
                    size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                )

    # --- Overlay label cards, e.g. "AQUA DOTS" — confirmed from reference screenshots ---
    if config.ENABLE_LABEL_CARDS:
        for i, seg in enumerate(segments):
            label = seg.get("label")
            if label and i < len(clips):
                safe_name = "".join(c if c.isalnum() else "_" for c in label)
                label_path = os.path.join(config.TEMP_DIR, f"label_{safe_name}.png")
                if not os.path.exists(label_path):
                    label_card.generate_label_card(label, label_path)
                label_clip = (
                    ImageClip(label_path)
                    .set_duration(clips[i].duration)
                    .resize(lambda t: 1.15 - 0.15 * min(t / 0.2, 1))  # quick pop-in
                    .set_position(("center", int(config.VIDEO_HEIGHT * 0.62)))
                )
                clips[i] = CompositeVideoClip(
                    [clips[i], label_clip],
                    size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                )

    video = concatenate_videoclips(clips, method="compose")

    # --- Watermark across the whole video (off by default, see config) ---
    if config.CHANNEL_WATERMARK_TEXT:
        wm_path = os.path.join(config.TEMP_DIR, "watermark.png")
        if not os.path.exists(wm_path):
            watermark.generate_watermark(config.CHANNEL_WATERMARK_TEXT, wm_path)
        wm_clip = ImageClip(wm_path).set_duration(video.duration)
        video = CompositeVideoClip([video, wm_clip], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

    # --- Build audio layers: voice + music + SFX ---
    voice = AudioFileClip(voice_path)
    audio_layers = [voice]

    if music_path and os.path.exists(music_path):
        music = AudioFileClip(music_path).volumex(0.12)
        music = audio_loop(music, duration=voice.duration)
        audio_layers.append(music)

    # SFX: whoosh at the start of each segment cut, ding on rank reveals
    whoosh_clip = sfx_manager.get_whoosh()
    ding_clip = sfx_manager.get_ding()

    if whoosh_clip or ding_clip:
        time_cursor = 0.0
        for i, dur in enumerate(segment_durations):
            if i > 0 and whoosh_clip:
                sfx = whoosh_clip.copy().set_start(time_cursor).volumex(0.6)
                audio_layers.append(sfx)

            if ding_clip and i < len(segments):
                rank = segments[i].get("rank")
                if rank is not None:
                    sfx = ding_clip.copy().set_start(time_cursor).volumex(0.8)
                    audio_layers.append(sfx)

            time_cursor += dur

    audio = CompositeAudioClip(audio_layers)
    video = video.set_audio(audio).set_duration(voice.duration)

    # --- Word-by-word captions (confirmed pattern, but kept toggle-able) ---
    if not config.ENABLE_WORD_CAPTIONS:
        video.write_videofile(
            output_path, fps=config.FPS, codec="libx264", audio_codec="aac",
            threads=4, preset="medium", logger=None,
        )
        return

    temp_path = output_path.replace(".mp4", "_no_captions.mp4")
    video.write_videofile(
        temp_path, fps=config.FPS, codec="libx264", audio_codec="aac",
        threads=4, preset="medium", logger=None,
    )

    escaped_caption_path = caption_path.replace("\\", "/").replace(":", "\\:")
    fonts_dir = os.path.dirname(config.FONT_PATH).replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y", "-i", temp_path,
        "-vf", f"ass={escaped_caption_path}:fontsdir={fonts_dir}",
        "-c:v", "libx264", "-c:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True)
    os.remove(temp_path)