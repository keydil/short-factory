"""
Generates the video script using the Gemini API.
Returns a dict: {"title": str, "segments": [{"text": str, "visual_keywords": [str,...], "rank": int|null, "label": str|null}, ...]}

Each segment is one "beat" of the video — a sentence of narration plus the visual
that should play under it. Splitting it this way is what lets the rest of the
pipeline cut visuals in sync with the voice, instead of one static image for 45s.
"""
import json
import time
from google import genai
import config

# New SDK uses a Client object instead of genai.configure() + GenerativeModel.
# pip install google-genai (the old google-generativeai package is deprecated
# and no longer receiving updates/bug fixes as of mid-2026).
client = genai.Client(api_key=config.GEMINI_API_KEY)


PROMPT_TEMPLATE = """You are a scriptwriter for a viral, faceless YouTube Shorts channel about {niche}.

Format: {format_instruction}

Write ONE short video script in {language_name}. Requirements:
- Hook in the very first sentence: a question or surprising claim that stops the scroll.
- Total spoken length: roughly {duration} seconds (about {word_count} words at natural speaking pace).
- Punchy, simple sentences, no filler words, no markdown.
- {outro_instruction}
- Split the narration into short segments (1 sentence each) for pacing.
- For each segment, give 2-3 KEYWORDS (in English, even if the script itself is in
  another language) describing a SPECIFIC visual moment or action that matches it —
  not an abstract concept. E.g. "hands assembling colorful beads" beats just "toy";
  "police evidence bag closeup" beats just "danger". Specific keywords pull footage
  that actually illustrates the claim instead of generic filler.
- For each segment also give a "rank" field. {rank_instruction}
- For each segment also give a "label" field — a short (1-4 word) ALL-CAPS-friendly
  on-screen text overlay for that beat: for the hook/intro segment, a punchy short
  version of the video title; for each ranked item segment, just that item's name;
  for a mid-video call-to-action segment, use EXACTLY "LIKE" or EXACTLY "SUBSCRIBE"
  (pick ONE based on whichever action that line emphasizes more — never combine
  them into one label); otherwise null if no distinct on-screen text fits that beat.

Return STRICT JSON only — no markdown fences, no commentary — in exactly this shape:
{{
  "title": "...",
  "segments": [
    {{"text": "...", "visual_keywords": ["...", "..."], "rank": null, "label": "..."}},
    ...
  ]
}}
"""

FORMAT_INSTRUCTIONS = {
    "top3": "A 'Top 3' countdown listicle (3 strangest/weirdest/most surprising things related to the niche).",
    "story": "A single fascinating fact, told as a short, surprising mini-story with a clear beginning, twist, and payoff.",
}

CTA_PATTERN_NOTE = (
    "For the CTA segment, use the 'silly conditional bait' format common in this genre — "
    "a lighthearted if/then that nudges different parts of the audience toward different "
    "actions, e.g. structure: 'If [condition A], like this video. If [condition B], "
    "subscribe.' The two conditions can be genuinely complementary (e.g. boys vs girls), "
    "intentionally redundant/silly so almost everyone qualifies (e.g. 'if your mom is a "
    "girl'), or tied to the video's own topic (e.g. 'if you've ever owned/seen [item from "
    "this video], like this video'). This format tends to also bait comments (people reply "
    "confirming which condition applies to them), which helps reach. Invent a FRESH pair of "
    "conditions each time you write a script — don't reuse the same phrasing twice."
)

RANK_INSTRUCTIONS = {
    "top3": (
        "This is a top3 countdown: set 'rank' to 3 on the segment that FIRST reveals item #3, "
        "2 on the segment that first reveals item #2, and 1 on the segment that first reveals item #1. "
        "Every other segment (hook, extra detail sentences, outro) gets 'rank': null. "
        "Right after the item #2 segment and BEFORE the item #1 segment, insert one short "
        "standalone CTA segment (rank: null, label: 'LIKE' or 'SUBSCRIBE'). " + CTA_PATTERN_NOTE
    ),
    "story": (
        "This format has no countdown, so 'rank' should be null for every segment. "
        "Partway through — after the hook but before the final twist/payoff — insert one "
        "short standalone CTA segment (label: 'LIKE' or 'SUBSCRIBE'). " + CTA_PATTERN_NOTE
    ),
}

OUTRO_INSTRUCTIONS = {
    "top3": (
        "For the very last segment: do NOT repeat 'like and subscribe' again — that was "
        "already covered by the mid-video CTA segment, and saying it twice in one short "
        "video reads as robotic repetition. Instead close with a short opinion-bait line "
        "tied to the specific items in THIS video, inviting a comment, e.g. 'Which one "
        "would you actually try?' or 'Comment which one surprised you most.'"
    ),
    "story": (
        "For the very last segment: do NOT repeat 'like and subscribe' again — that was "
        "already covered by the earlier CTA segment, and saying it twice in one short video "
        "reads as robotic repetition. Instead close with a short line inviting a reaction "
        "in the comments related to the fact, e.g. 'Would you have guessed this?' or "
        "'Comment if you already knew this.'"
    ),
}

LANGUAGE_NAMES = {"en": "English", "id": "Bahasa Indonesia"}


def generate_script(topic_hint: str = None) -> dict:
    words_per_second = 2.5  # rough average speaking pace for narration
    word_count = int(config.TARGET_DURATION_SECONDS * words_per_second)

    prompt = PROMPT_TEMPLATE.format(
        niche=config.NICHE_DESCRIPTION,
        format_instruction=FORMAT_INSTRUCTIONS[config.CONTENT_FORMAT],
        rank_instruction=RANK_INSTRUCTIONS[config.CONTENT_FORMAT],
        outro_instruction=OUTRO_INSTRUCTIONS[config.CONTENT_FORMAT],
        language_name=LANGUAGE_NAMES[config.LANGUAGE],
        duration=config.TARGET_DURATION_SECONDS,
        word_count=word_count,
    )
    if topic_hint:
        prompt += f"\nSpecific topic to use: {topic_hint}\n"

    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            break
        except Exception as e:
            is_rate_limit = getattr(e, "code", None) == 429 or "429" in str(e)
            if is_rate_limit:
                if attempt < max_retries - 1:
                    wait_s = 25
                    print(f"\n     [!] API limit reached. Waiting {wait_s}s before retry (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_s)
                else:
                    raise e
            else:
                raise e

    raw = response.text.strip()
    # Gemini sometimes wraps JSON in ```json fences despite instructions not to - strip defensively
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw[4:] if raw.startswith("json") else raw

    return json.loads(raw.strip())


if __name__ == "__main__":
    # Quick standalone test: python modules/script_generator.py
    script = generate_script()
    print(json.dumps(script, indent=2, ensure_ascii=False))