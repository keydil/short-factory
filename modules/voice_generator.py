"""
Turns narration text into a voiceover mp3 using free Microsoft Edge neural voices,
and captures (or approximates) word-level timing so we can build animated,
word-by-word captions later — that's the single biggest visual upgrade for making
automated content look "professionally edited".

Note: edge-tts's internal word-boundary event format has shifted between versions
before. The try/except below falls back to an even time split across the real
audio duration if that happens, so the pipeline keeps working either way.
"""
import asyncio
import sys
import edge_tts
from moviepy.editor import AudioFileClip
import config

# Fix for Windows: aiodns requires SelectorEventLoop, not the default ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _generate(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, config.TTS_VOICE)
    word_boundaries = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(chunk)

    return word_boundaries


def _to_seconds(value):
    # edge-tts reports offset/duration in 100-nanosecond units
    return value / 10_000_000


def generate_voice(text: str, output_path: str):
    """
    Returns [{"word": str, "start": float_seconds, "end": float_seconds}, ...]
    """
    boundaries = asyncio.run(_generate(text, output_path))

    words = []
    try:
        for b in boundaries:
            start = _to_seconds(b["offset"])
            duration = _to_seconds(b["duration"])
            words.append({"word": b["text"], "start": start, "end": start + duration})
        if not words:
            raise ValueError("no word boundaries returned by edge-tts")
    except (KeyError, ValueError):
        print("  (!) word-boundary timing unavailable, falling back to even split")
        audio_duration = AudioFileClip(output_path).duration
        raw_words = text.split()
        per_word = audio_duration / max(len(raw_words), 1)
        words = [
            {"word": w, "start": i * per_word, "end": (i + 1) * per_word}
            for i, w in enumerate(raw_words)
        ]

    return words
