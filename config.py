"""
Central configuration for the AI Shorts Factory pipeline.
Edit the values here before running main.py. API keys go in a .env file
(copy .env.example to .env and fill it in) — never commit real keys to git.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- API Keys ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

# ---- Content settings ----
# "en" = English (bigger global reach, better ad RPM, matches the reference channels)
# "id" = Bahasa Indonesia
LANGUAGE = "en"

# "top3"  -> listicle format, ala @3intheworld ("3 strangest things about X")
# "story" -> single fact told as a short story, ala @NarratoChannel
CONTENT_FORMAT = "story"

# Be specific here — this becomes part of the AI prompt and shapes everything.
NICHE_DESCRIPTION = "bizarre and little-known facts about history, science, and the natural world"

# Gemini model. The "-latest" alias auto-points to Google's current flash model,
# so this won't silently break when a specific snapshot gets retired.
# Check https://ai.google.dev/gemini-api/docs/models if this ever errors out.
GEMINI_MODEL = "gemini-flash-latest"

# ---- Video settings ----
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
# Suggested pacing differs a lot by format. Based on an actual @3intheworld
# video transcript ("3 dangerous toys in the world"), a 3-item top3 countdown
# runs just ~26 seconds total — much punchier than a single-story format.
DURATION_BY_FORMAT = {"top3": 28, "story": 45}
TARGET_DURATION_SECONDS = DURATION_BY_FORMAT[CONTENT_FORMAT]

# ---- Voice settings ----
# Run `edge-tts --list-voices` in your terminal to browse all available voices.
TTS_VOICE = "en-US-AndrewNeural" if LANGUAGE == "en" else "id-ID-ArdiNeural"

# ---- Paths ----
OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")   # drop your own royalty-free tracks here
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")       # drop whoosh.mp3 / ding.mp3 here, see README
MANUAL_VEO_DIR = os.path.join(ASSETS_DIR, "manual_veo")  # for clips you generate by hand in Flow
TEMP_DIR = "temp"

# ---- Polish settings (the stuff that makes it feel "professionally edited") ----
# Free, commercially-usable "bouncy cartoon" font (Apache licensed), matches the
# style seen in real reference videos for this niche. Already bundled in assets/fonts/.
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "LuckiestGuy-Regular.ttf")
TEXT_FILL_COLOR = (255, 221, 0, 255)     # yellow, matches reference title cards
TEXT_OUTLINE_COLOR = (0, 0, 0, 255)      # black outline

ENABLE_LABEL_CARDS = True    # big on-screen text per beat (e.g. "AQUA DOTS") - confirmed from reference
ENABLE_WORD_CAPTIONS = True  # word-by-word spoken captions - CONFIRMED, cycles through CAPTION_COLOR_CYCLE
CAPTION_COLOR_CYCLE = [(255, 255, 255), (255, 221, 0), (0, 229, 255)]  # white, yellow, aqua - confirmed pattern
ENABLE_RANK_BADGES = False   # circular "#3/#2/#1" badge - NOT seen in the reference video, off by default
ENABLE_SFX = True            # whoosh on cuts, ding on reveals — see assets/sfx/

# Channel handle shown as a faint repeated watermark across the frame, like
# "YT: 3INTHEWORLD" in the reference. Leave as "" to disable.
CHANNEL_WATERMARK_TEXT = ""