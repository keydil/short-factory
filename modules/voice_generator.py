"""
Turns narration text into voiceover audio using free Microsoft Edge neural voices.

Two entry points:
- generate_voice(text, output_path) — original single-shot version: one TTS call
  for a whole block of text. Handy for quick standalone tests.
- generate_voice_for_script(segments, output_dir) — generates TTS PER SEGMENT with
  slightly different pacing per beat (hook punchier, CTA playful, final line eases
  off), then places them on one timeline with small silence gaps between lines —
  longer before a reveal/CTA, like a real narrator pausing for effect. This is the
  single biggest lever for making an automated voiceover feel less robotic: a flat,
  relentless, identically-paced wall of speech is one of the most obvious "AI" tells.

Note: edge-tts's internal word-boundary event format has shifted between versions
before. The try/except below falls back to an even time split across the real
audio duration if that happens, so the pipeline keeps working either way.
"""
import asyncio
import os
import sys
import edge_tts
from moviepy.editor import AudioFileClip, CompositeAudioClip
import config

# Fix for Windows: aiodns requires SelectorEventLoop, not the default ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _generate(text: str, output_path: str, rate: str = "+0%", volume: str = "+0%"):
    communicate = edge_tts.Communicate(text, config.TTS_VOICE, rate=rate, volume=volume)
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


def _synthesize(text: str, output_path: str, rate: str = "+0%", volume: str = "+0%"):
    """Runs one TTS call, returns LOCAL (0-based) word timings for that text alone."""
    boundaries = asyncio.run(_generate(text, output_path, rate, volume))

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


def generate_voice(text: str, output_path: str, rate: str = "+0%", volume: str = "+0%"):
    """Original single-shot version — one TTS call for a whole block of text."""
    return _synthesize(text, output_path, rate, volume)


def _pick_rate_for_segment(seg: dict, index: int, total: int) -> str:
    """
    Small heuristic so the narration isn't one flat, robotic tone throughout —
    real narrators speed up for the hook, ease off for emphasis, etc.
    Percentages are a starting point, tweak freely.
    """
    label = (seg.get("label") or "").upper()
    if index == 0:
        return "+8%"       # hook - energetic, grabs attention fast
    if label in ("LIKE", "SUBSCRIBE"):
        return "+12%"      # CTA - quick and playful, doesn't overstay its welcome
    if index == total - 1:
        return "-4%"       # final line - slight ease-off gives the payoff some weight
    return "+2%"            # default - just a touch livelier than dead-neutral


def generate_voice_for_script(segments: list, output_dir: str):
    """
    Generates TTS per-segment (each with its own pacing), places them on one
    timeline with small silence gaps for breathing room, and returns everything
    the rest of the pipeline needs in one go.

    Returns: (combined_audio_path, word_timings, segment_durations)
    - word_timings are ABSOLUTE (already offset to match the combined timeline)
    - segment_durations[i] = that segment's spoken length + any trailing gap,
      so visual cuts stay perfectly in sync even though there's a pause moviepy
      never explicitly renders as its own clip.
    """
    os.makedirs(output_dir, exist_ok=True)
    positioned_clips = []
    word_timings = []
    segment_durations = []
    running_time = 0.0

    for i, seg in enumerate(segments):
        rate = _pick_rate_for_segment(seg, i, len(segments))
        seg_path = os.path.join(output_dir, f"voice_seg_{i}.mp3")
        local_words = _synthesize(seg["text"], seg_path, rate=rate)

        for w in local_words:
            word_timings.append({
                "word": w["word"],
                "start": w["start"] + running_time,
                "end": w["end"] + running_time,
            })

        seg_clip = AudioFileClip(seg_path)
        positioned_clips.append(seg_clip.set_start(running_time))
        seg_duration = seg_clip.duration
        running_time += seg_duration

        if i < len(segments) - 1:
            next_seg = segments[i + 1]
            is_big_beat = (
                next_seg.get("rank") is not None
                or (next_seg.get("label") or "").upper() in ("LIKE", "SUBSCRIBE")
            )
            gap_s = 0.28 if is_big_beat else 0.09  # longer pause before a reveal/CTA
            running_time += gap_s
            seg_duration += gap_s

        segment_durations.append(seg_duration)

    combined = CompositeAudioClip(positioned_clips).set_duration(running_time)
    combined_path = os.path.join(output_dir, "voice_combined.mp3")
    combined.write_audiofile(combined_path, fps=positioned_clips[0].fps, logger=None)

    return combined_path, word_timings, segment_durations