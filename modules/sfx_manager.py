"""
Manages sound effects (whoosh on segment transitions, ding on rank reveals).
Gracefully degrades if SFX files aren't present — the pipeline keeps running,
you just won't hear those effects until you drop the files in assets/sfx/.
"""
import os
from moviepy.editor import AudioFileClip
import config


def _load_sfx(filename: str):
    """Try to load an SFX file, return None if missing or SFX disabled."""
    if not config.ENABLE_SFX:
        return None
    path = os.path.join(config.SFX_DIR, filename)
    if os.path.exists(path):
        return AudioFileClip(path)
    return None


def get_whoosh():
    """Short whoosh/transition sound played at each segment cut."""
    return _load_sfx("whoosh.mp3")


def get_ding():
    """Ding/pop sound played when a rank badge appears (top3 format)."""
    return _load_sfx("ding.mp3")
