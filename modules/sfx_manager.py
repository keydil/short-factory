"""
The "soundboard" — layers short sound effects into the final audio mix. Each
function loads one named file from assets/sfx/ if it exists, or returns None
(silently skipped) if you haven't downloaded it yet — so the pipeline keeps
working while you fill the soundboard in gradually.

Where to get free SFX: https://mixkit.co/free-sound-effects/ — no account, no
attribution required, explicitly cleared for commercial use. Search terms for
each slot are in the README.

(Deliberately not pulling from sites like myinstants.com — that's mostly
unlicensed reuploads of movie/game/meme audio, which is exactly the kind of
thing that gets a monetized channel hit with a copyright claim.)
"""
import os
from moviepy.editor import AudioFileClip
import config


def _load_sfx(filename: str):
    if not config.ENABLE_SFX:
        return None
    path = os.path.join(config.SFX_DIR, filename)
    if os.path.exists(path):
        return AudioFileClip(path)
    return None


def get_whoosh():
    """Transition sound played at every segment cut."""
    return _load_sfx("whoosh.mp3")


def get_pop():
    """Pop/click sound for a plain title or item-name label revealing."""
    return _load_sfx("pop.mp3") or _load_sfx("ding.mp3")  # ding.mp3 kept as a fallback name


def get_bell():
    """Notification-bell sound, specifically for the SUBSCRIBE badge (it has a bell icon)."""
    return _load_sfx("bell.mp3") or _load_sfx("ding.mp3")


def get_like_pop():
    """Punchier pop sound, specifically for the LIKE badge."""
    return _load_sfx("like_pop.mp3") or _load_sfx("pop.mp3") or _load_sfx("ding.mp3")


def get_riser():
    """Short tension build-up played leading into the final/best reveal (top3 rank #1)."""
    return _load_sfx("riser.mp3")


def get_hook_hit():
    """Sharp impact/hit sound right as the video opens on the hook."""
    return _load_sfx("hook_hit.mp3")