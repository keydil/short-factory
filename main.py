"""
AI Shorts Factory - end to end pipeline.

Usage:
    python main.py                          # AI picks the topic
    python main.py "topic hint goes here"   # you give the AI a starting topic
"""
import sys
import os
import json
from datetime import datetime

import config
from modules import script_generator, voice_generator, visual_fetcher, caption_generator, video_assembler


def run(topic_hint: str = None):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)

    print("1/5  Writing script with Gemini...")
    script = script_generator.generate_script(topic_hint)
    print(f"     Title: {script['title']}")

    full_text = " ".join(seg["text"] for seg in script["segments"])

    print("2/5  Generating voiceover...")
    voice_path = os.path.join(config.TEMP_DIR, "voice.mp3")
    word_timings = voice_generator.generate_voice(full_text, voice_path)

    print("3/5  Fetching visuals for each segment...")
    segment_durations = []
    visuals = []
    word_cursor = 0
    for i, seg in enumerate(script["segments"]):
        n_words = len(seg["text"].split())
        seg_words = word_timings[word_cursor:word_cursor + n_words]
        word_cursor += n_words
        duration = (seg_words[-1]["end"] - seg_words[0]["start"]) if seg_words else 3.0
        segment_durations.append(max(duration, 1.5))

        visual = visual_fetcher.fetch_visual_for_segment(
            seg["visual_keywords"], os.path.join(config.TEMP_DIR, "visuals"), i
        )
        visuals.append(visual)
        print(f"     segment {i + 1}/{len(script['segments'])}: {visual['type']} ({seg['visual_keywords'][0]})")

    print("4/5  Building animated captions...")
    caption_path = os.path.join(config.TEMP_DIR, "captions.ass")
    caption_generator.build_caption_file(word_timings, caption_path)

    print("5/5  Assembling final video (this can take a minute)...")
    music_path = None
    if os.path.isdir(config.MUSIC_DIR):
        tracks = [f for f in os.listdir(config.MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if tracks:
            music_path = os.path.join(config.MUSIC_DIR, tracks[0])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(config.OUTPUT_DIR, f"short_{timestamp}.mp4")

    video_assembler.assemble_video(
        visuals, segment_durations, script["segments"], voice_path, music_path, caption_path, output_path
    )

    with open(output_path.replace(".mp4", "_script.json"), "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    print(f"\nDone! -> {output_path}")
    print("Don't forget to manually review it before posting, and tick the")
    print("'Altered or synthetic content' toggle in YouTube Studio if it applies.")


if __name__ == "__main__":
    hint = sys.argv[1] if len(sys.argv) > 1 else None
    run(hint)
